from flask import Flask, request, jsonify
from flask_cors import CORS
import redis
import json
import random
import hashlib
import re
from opentelemetry import trace, metrics
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
import logging
import os
from datetime import datetime
import openai

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize OpenTelemetry
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

otlp_exporter = OTLPSpanExporter(
    endpoint=os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT', 'http://localhost:4318') + '/v1/traces',
)

span_processor = BatchSpanProcessor(otlp_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

# Instrument Flask and requests
FlaskInstrumentor().instrument_app(app)
RequestsInstrumentor().instrument()

# Redis connection
redis_client = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379'))

# OpenAI configuration (optional - will fallback to template-based generation)
openai_api_key = os.getenv('OPENAI_API_KEY')
if openai_api_key:
    openai.api_key = openai_api_key
    USE_AI = True
else:
    USE_AI = False
    logger.info("OpenAI API key not found, using template-based generation")

# Prompt templates for fallback generation
PROMPT_TEMPLATES = {
    'Fantasy': [
        {
            'title': 'The Last Dragon\'s Secret',
            'template': 'In a world where dragons were thought extinct, {character} discovers {discovery} hidden in {location}. As {conflict} threatens the realm, they must {challenge} before {deadline}.',
            'elements': {
                'character': ['a young apprentice mage', 'an exiled knight', 'a street thief with unusual talents'],
                'discovery': ['a dragon egg', 'an ancient prophecy', 'a map to the dragon sanctuary'],
                'location': ['the royal library\'s forbidden section', 'an abandoned tower', 'beneath the city sewers'],
                'conflict': ['a dark sorcerer\'s army', 'a plague of shadows', 'civil war'],
                'challenge': ['master forbidden magic', 'unite warring kingdoms', 'awaken the sleeping dragon'],
                'deadline': ['the blood moon rises', 'winter\'s first snow', 'the king\'s coronation']
            }
        }
    ],
    'Science Fiction': [
        {
            'title': 'Colony Ship Paradox',
            'template': 'The generation ship {ship_name} has been traveling for {duration}, but {character} discovers {revelation}. With {resource} running low and {threat} approaching, they must decide whether to {choice}.',
            'elements': {
                'ship_name': ['Horizon\'s Hope', 'New Eden', 'Stellar Ark'],
                'duration': ['300 years', '50 generations', 'longer than recorded history'],
                'character': ['the ship\'s AI maintenance tech', 'a historian studying old Earth', 'the youngest council member'],
                'revelation': ['they\'ve been traveling in circles', 'Earth still exists', 'the ship is actually a prison'],
                'resource': ['oxygen', 'genetic diversity', 'hope'],
                'threat': ['an alien armada', 'system-wide cascade failure', 'a mutiny'],
                'choice': ['wake the frozen founders', 'change course to an unknown planet', 'reveal the truth to everyone']
            }
        }
    ],
    'Mystery': [
        {
            'title': 'The Vanishing Gallery',
            'template': '{character} arrives at {location} to investigate {mystery}. The only clue is {clue}, but {complication} makes everyone a suspect. The truth involves {twist}.',
            'elements': {
                'character': ['a retired detective', 'an insurance investigator', 'an art student'],
                'location': ['a private island museum', 'a underground auction house', 'a restored Victorian mansion'],
                'mystery': ['the disappearance of priceless paintings', 'a murder during a locked-room auction', 'forged masterpieces appearing worldwide'],
                'clue': ['a half-burned photograph', 'a coded message in the victim\'s notebook', 'paint that shouldn\'t exist yet'],
                'complication': ['everyone has an alibi', 'the security footage has been edited', 'the victim is still alive'],
                'twist': ['time travel', 'identical twins nobody knew about', 'the detective is the criminal']
            }
        }
    ],
    'Horror': [
        {
            'title': 'The Inheritance',
            'template': '{character} inherits {inheritance} from {relative}, but discovers {horror} lurking within. As {event} approaches, they realize {revelation} and must {action} to survive.',
            'elements': {
                'character': ['a struggling artist', 'a medical student', 'a single parent'],
                'inheritance': ['a Victorian mansion', 'an antique shop', 'a storage unit full of artifacts'],
                'relative': ['an uncle they never knew existed', 'their recently deceased grandmother', 'a distant cousin'],
                'horror': ['the previous owners never left', 'a portal to somewhere else', 'a curse that transfers to the new owner'],
                'event': ['the anniversary of a tragedy', 'a lunar eclipse', 'their first night alone'],
                'revelation': ['they were chosen for a reason', 'their family has kept this secret for generations', 'escaping makes it worse'],
                'action': ['perform an ancient ritual', 'burn everything', 'make a terrible sacrifice']
            }
        }
    ],
    'Romance': [
        {
            'title': 'Second Chances',
            'template': '{character1} and {character2} meet again after {time_period} at {location}. Despite {obstacle}, they discover {connection}, but {conflict} threatens to {consequence}.',
            'elements': {
                'character1': ['a successful CEO', 'a small-town teacher', 'a traveling musician'],
                'character2': ['their college sweetheart', 'their former rival', 'their best friend\'s sibling'],
                'time_period': ['ten years', 'a lifetime', 'one unforgettable summer'],
                'location': ['a destination wedding', 'their hometown reunion', 'an unexpected flight delay'],
                'obstacle': ['they\'re both engaged to others', 'a bitter misunderstanding', 'completely different lives now'],
                'connection': ['they still finish each other\'s sentences', 'a shared dream they never forgot', 'letters never sent'],
                'conflict': ['a job opportunity abroad', 'family disapproval', 'a secret from the past'],
                'consequence': ['separate them forever', 'change everything', 'break other hearts']
            }
        }
    ]
}

def get_random_word_count_and_difficulty():
    """Randomly select word count and corresponding difficulty with weighted probabilities"""
    import random
    
    # Options with (word_count, difficulty, weight)
    # Very Easy: 30%, Easy: 30%, Medium: 25%, Hard: 15%
    options = [
        (250, 'Very Easy', 30),
        (500, 'Easy', 30),
        (750, 'Medium', 25),
        (1000, 'Hard', 15)
    ]
    
    # Extract choices and weights
    choices = [(wc, diff) for wc, diff, _ in options]
    weights = [weight for _, _, weight in options]
    
    # Use random.choices for weighted selection
    word_count, difficulty = random.choices(choices, weights=weights, k=1)[0]
    return word_count, difficulty

def generate_prompt_from_template(genres):
    """Generate a writing prompt using templates when AI is not available"""
    selected_templates = []
    
    for genre in genres:
        if genre in PROMPT_TEMPLATES:
            selected_templates.extend(PROMPT_TEMPLATES[genre])
    
    if not selected_templates:
        # Default template if no matching genres
        selected_templates = [
            {
                'title': 'The Unexpected Journey',
                'template': 'Your protagonist discovers {discovery} that changes everything they believed about {belief}. They must {action} before {deadline}.',
                'elements': {
                    'discovery': ['a hidden letter', 'a secret door', 'an old photograph'],
                    'belief': ['their family history', 'their own identity', 'the nature of reality'],
                    'action': ['uncover the truth', 'make an impossible choice', 'confront their fears'],
                    'deadline': ['it\'s too late', 'someone else finds out', 'the opportunity disappears']
                }
            }
        ]
    
    # Select random template
    template_data = random.choice(selected_templates)
    template = template_data['template']
    elements = template_data['elements']
    
    # Fill in the template
    prompt_text = template
    for key, options in elements.items():
        prompt_text = prompt_text.replace(f'{{{key}}}', random.choice(options))
    
    # Get random word count and difficulty
    word_count, difficulty = get_random_word_count_and_difficulty()    
    return {
        'title': template_data['title'],
        'content': prompt_text,
        'genres': genres,
        'difficulty': difficulty,
        'wordCount': word_count,
        'tips': generate_writing_tips(genres),
        'timestamp': datetime.utcnow().isoformat()
    }


def generate_prompt_with_ai(genres):
    """Generate creative writing exercises focused on skill-building"""
    import random
    import re
    
    genre_string = ", ".join(genres)
    
    exercise_types = [
        {
            "name": "Idea Generation Drill",
            "prompt": f"""Create an idea generation exercise for {genre_string} writing. 

Format:
**Exercise Name**: [Creative name]
**Goal**: [One sentence - what skill this develops]
**Exercise**: [Clear instructions explaining the drill]
**Example Progression**: [Show 3 examples from simple to unusual]
**Pro Tip**: [One sentence advice]

At the end, add a section:
**Writing Tips for This Exercise**:
- [Tip 1 specific to this exercise]
- [Tip 2 specific to this exercise]  
- [Tip 3 specific to this exercise]

NO character names. Focus on the TECHNIQUE of generating ideas."""
        },
        {
            "name": "World-Building Technique",
            "prompt": f"""Create a world-building exercise for {genre_string}.

Format:
**Technique Name**: [Name]
**Goal**: [What this teaches]
**Exercise**: [Instructions for the technique, 200-250 words]
**Rules**:
- [What to do]
- [What to avoid]
**Example Approach**: [2-3 sentences showing the METHOD]

At the end, add:
**Writing Tips for This Exercise**:
- [Tip 1 specific to world-building technique]
- [Tip 2 specific to world-building technique]
- [Tip 3 specific to world-building technique]

NO character names. Teach the CRAFT."""
        },
        {
            "name": "Structural Exercise",
            "prompt": f"""Create a structural writing exercise for {genre_string}.

Format:
**Structure Technique**: [Name]
**Goal**: [What this teaches about story structure]
**The Exercise**: [Explain the structural technique]
**Rules**: [Structural constraints and what they teach]
**Application**: [How to apply in 500 words]

At the end, add:
**Writing Tips for This Exercise**:
- [Tip 1 about story structure]
- [Tip 2 about story structure]
- [Tip 3 about story structure]

Focus on STRUCTURE and TECHNIQUE."""
        },
        {
            "name": "Description Technique",
            "prompt": f"""Create a descriptive writing exercise for {genre_string}.

Format:
**Description Technique**: [Name]
**Goal**: [What skill this builds]
**The Challenge**: [Explain the descriptive technique]
**Requirements**:
- [Technical requirement 1]
- [Technical requirement 2]
- [Word count: 300-400 words]
**Forbidden**: [Generic words/habits to avoid]

At the end, add:
**Writing Tips for This Exercise**:
- [Tip 1 about descriptive writing]
- [Tip 2 about descriptive writing]
- [Tip 3 about descriptive writing]

Teach CRAFT of description."""
        },
        {
            "name": "Dialogue Craft",
            "prompt": f"""Create a dialogue craft exercise for {genre_string}.

Format:
**Dialogue Technique**: [Name]
**Goal**: [What this teaches about dialogue]
**The Exercise**: [Instructions on HOW to write dialogue]
**What Dialogue Should Reveal**: [3 elements]
**Technical Rules**: [2 dialogue rules]

At the end, add:
**Writing Tips for This Exercise**:
- [Tip 1 about dialogue craft]
- [Tip 2 about dialogue craft]
- [Tip 3 about dialogue craft]

Focus on dialogue CRAFT."""
        },
        {
            "name": "Theme & Subtext",
            "prompt": f"""Create a theme/subtext exercise for {genre_string}.

Format:
**Exercise Name**: [Name]
**Goal**: [What this teaches about theme]
**The Challenge**: [How to embed theme without preaching]
**Approach**: [2-3 techniques for showing theme]
**Practice**: [How to practice this skill in 300-500 words]

At the end, add:
**Writing Tips for This Exercise**:
- [Tip 1 about theme and subtext]
- [Tip 2 about theme and subtext]
- [Tip 3 about theme and subtext]

Teach TECHNIQUE of thematic writing."""
        },
        {
            "name": "Genre Convention Study",
            "prompt": f"""Create a genre study exercise for {genre_string}.

Format:
**Genre Exercise**: [Name]
**Goal**: [What this teaches about genre craft]
**The Exercise**: [Instructions for working with genre conventions]
**Genre Mashup Option**: [How to combine {genre_string} with another genre]
**What You'll Learn**: [2 skills]

At the end, add:
**Writing Tips for This Exercise**:
- [Tip 1 about genre conventions]
- [Tip 2 about genre conventions]
- [Tip 3 about genre conventions]

Focus on GENRE as craft tool."""
        },
        {
            "name": "Reverse Engineering",
            "prompt": f"""Create a reverse engineering exercise for {genre_string}.

Format:
**Analysis Exercise**: [Name]
**Goal**: [What this teaches about story construction]
**The Exercise**: Pick a {genre_string} story you admire. Analyze:
- [Element 1 to outline]
- [Element 2 to outline]
- [Element 3 to outline]
- [Element 4 to outline]
**Then**: [What to do with this analysis]
**What You'll Learn**: [The technique this reveals]

At the end, add:
**Writing Tips for This Exercise**:
- [Tip 1 about analyzing stories]
- [Tip 2 about analyzing stories]
- [Tip 3 about analyzing stories]

Teach ANALYTICAL skills."""
        },
        {
            "name": "Constraint Creativity",
            "prompt": f"""Create a constraint-based exercise for {genre_string}.

Format:
**Constraint Exercise**: [Name]
**Goal**: [What this constraint teaches]
**The Constraint**: [Specific limitation and why it's useful]
**How to Apply It**: [Instructions for using this constraint in 500-750 words]
**What This Teaches**: [The craft skill forced by this constraint]

At the end, add:
**Writing Tips for This Exercise**:
- [Tip 1 about working with constraints]
- [Tip 2 about working with constraints]
- [Tip 3 about working with constraints]

Focus on constraints as LEARNING TOOLS."""
        },
        {
            "name": "Revision Technique",
            "prompt": f"""Create a revision exercise for {genre_string}.

Format:
**Revision Technique**: [Name]
**Goal**: [What editing skill this builds]
**The Exercise**: Take any draft and apply this technique:
[Specific revision approach step-by-step]
**What to Look For**: [3 red flags]
**The Fix**: [How to revise each issue]

At the end, add:
**Writing Tips for This Exercise**:
- [Tip 1 about revision and editing]
- [Tip 2 about revision and editing]
- [Tip 3 about revision and editing]

Teach REVISION as craft skill."""
        }
    ]
    
    exercise_type = random.choice(exercise_types)
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a creative writing instructor teaching techniques and skills. Create exercises that are instructional and teach craft, not story prompts. Avoid character names and specific scenarios. Focus on teaching HOW to write. Always include 3 specific writing tips tailored to the exercise."},
                {"role": "user", "content": exercise_type["prompt"]}
            ],
            temperature=0.85,
            max_tokens=800,
            presence_penalty=0.7,
            frequency_penalty=0.7
        )
        
        content = response.choices[0].message.content
        
        # Extract title
        title = None
        lines = content.split('\n')
        for line in lines[:5]:
            line = line.strip()
            if line.startswith('**') or line.startswith('#'):
                title = line.replace('**', '').replace('#', '').strip()
                if title and len(title) > 3 and len(title) < 100:
                    break
        
        if not title:
            title = f"{exercise_type['name']}: {genre_string}"
        
        # Extract writing tips from the content
        tips = []
        content_without_tips = content
        
        # Find the "Writing Tips" section
        tip_section_match = re.search(r'\*\*Writing Tips.*?\*\*:?\s*\n(.*?)(?=\n\n|\Z)', content, re.DOTALL | re.IGNORECASE)
        
        if tip_section_match:
            tip_section = tip_section_match.group(1)
            
            # Extract individual tips
            for line in tip_section.split('\n'):
                line = line.strip()
                if line.startswith('-') or line.startswith('•') or line.startswith('*'):
                    tip = re.sub(r'^[-•*]\s*', '', line).strip()
                    if tip and len(tip) > 10:
                        tips.append(tip)
            
            # Remove the entire "Writing Tips" section from content
            content_without_tips = re.sub(r'\*\*Writing Tips.*?\*\*:?\s*\n.*?(?=\n\n|\Z)', '', content, flags=re.DOTALL | re.IGNORECASE)
            content_without_tips = content_without_tips.strip()
        
        # Fallback to generic tips if none found
        if not tips:
            tips = [
                f"Practice this exercise regularly to build muscle memory for {exercise_type['name'].lower()}",
                "Don't edit while doing the exercise - focus on exploration first",
                "Review your work after completing the exercise to identify patterns"
            ]
        
        word_count, difficulty = get_random_word_count_and_difficulty()
        
        return {
            'title': title,
            'content': content_without_tips,  # Content WITHOUT the tips section
            'genres': genres,
            'difficulty': difficulty,
            'wordCount': word_count,
            'exerciseType': exercise_type['name'],
            'tips': tips[:3],  # Tips extracted separately, only first 3
            'timestamp': datetime.utcnow().isoformat(),
            'ai_generated': True
        }
    except Exception as e:
        logger.error(f"AI generation failed: {str(e)}")
        return generate_prompt_from_template(genres)

def generate_writing_tips(genres):
    """Generate writing tips based on selected genres"""
    tips = []
    
    genre_tips = {
        'Fantasy': 'Build a consistent magic system with clear rules and limitations.',
        'Science Fiction': 'Ground your technology in real scientific concepts, even if extrapolated.',
        'Mystery': 'Plant clues fairly throughout the story - readers should be able to solve it.',
        'Horror': 'Build tension through atmosphere and pacing, not just jump scares.',
        'Romance': 'Develop both characters fully - they should be interesting apart and together.',
        'Thriller': 'Keep the pacing tight and end chapters with hooks.',
        'Historical Fiction': 'Research the period thoroughly but don\'t let facts overwhelm the story.',
        'Literary Fiction': 'Focus on character development and thematic depth.',
        'Young Adult': 'Address serious themes while maintaining an authentic teen voice.',
        'Crime': 'Make your detective\'s process logical and methodical.',
        'Adventure': 'Balance action sequences with character moments.',
        'Dystopian': 'Create a believable path from our world to yours.',
        'Magical Realism': 'Treat magical elements as mundane parts of the world.',
        'Western': 'Focus on themes of justice, freedom, and survival.',
        'Biography': 'Find the narrative arc in real events.',
        'Self-Help': 'Provide actionable advice with real-world examples.',
        'Philosophy': 'Make abstract concepts concrete through examples.',
        'Poetry': 'Show rather than tell - use vivid imagery.'
    }
    
    for genre in genres:
        if genre in genre_tips:
            tips.append(genre_tips[genre])
    
    # Add general tips
    tips.append('Start with a strong opening line that immediately engages the reader.')
    tips.append('Show character growth through actions and decisions, not just description.')
    
    return tips[:3]  # Return top 3 tips

def generate_sound_design_prompt(synthesizer, exercise_type):
    """Generate sound design exercises for electronic music production"""

    # Synthesizer capabilities and context
    synth_context = {
        'Serum 2': {
            'type': 'wavetable',
            'features': 'advanced modulation matrix, visual feedback, effects rack, wavetable editor',
            'strengths': 'complex modulation routing, visual waveform manipulation, FM synthesis'
        },
        'Phase Plant': {
            'type': 'modular',
            'features': 'snapin effects, flexible routing, multiple oscillator types',
            'strengths': 'modular signal flow, creative effects combinations, harmonic oscillators'
        },
        'Vital': {
            'type': 'wavetable',
            'features': 'spectral warping, advanced modulation, free and open-source',
            'strengths': 'spectral effects, stereo modulation, filter morphing'
        }
    }

    if not USE_AI:
        # Fallback templates for sound design
        if exercise_type == 'technical':
            templates = {
                'Serum 2': [
                    "Create a Skrillex-style metallic bass using FM modulation with detuned oscillators and harsh filtering",
                    "Design a Virtual Riot supersized growl with heavy unison (8+ voices), movement automation, and vowel-like filter morphing",
                    "Build a Space Laces glitchy lead with rapid wavetable morphing, chaos modulation, and pitch shifting",
                    "Create a Tchami future house bass using filtered square waves with punchy envelope and subtle pitch modulation",
                    "Design a G Jones experimental texture using custom wavetables, extreme modulation routing, and unconventional LFO rates",
                    "Build a Chee-style neuro bass with complex FM routing, filter drive saturation, and rhythmic modulation",
                    "Create a Resonant Language organic lead using evolving wavetables, subtle detuning, and harmonic filtering",
                    "Design a Noisia reese bass with multiple detuned saw waves, precise filter automation, and subtle movement",
                    "Build an Eptic heavy riddim bass using square wave FM, aggressive filtering, and pitch envelope modulation",
                    "Create an Esseks wonky mid-bass with wavetable morphing, stereo movement, and creative modulation routing",
                    "Design a Mr. Bill glitchy texture using rapid wavetable scanning, micro-modulation, and rhythmic gating",
                    "Build a Charlesthefirst melodic bass using warm wavetables, filter movement, and subtle portamento"
                ],
                'Phase Plant': [
                    "Create an Eprom heavy bass using layered oscillators with distortion snapins and parallel processing chains",
                    "Design a Tipper-style surgical bass with modular signal flow, precise filter automation, and subtle harmonic movement",
                    "Build a Culprate atmospheric texture combining multiple oscillator types with creative snapin effect routing",
                    "Create a Koan Sound neurofunk bass using harmonic oscillators, modular routing, and aggressive distortion staging",
                    "Design a Kursa experimental sound using non-standard oscillator combinations and unconventional effect chains",
                    "Build a Seppa downtempo lead with smooth oscillator blending, modular filter routing, and spatial effects",
                    "Create a Vorso glitch bass using granular-style oscillator manipulation and complex modulation matrices",
                    "Design a Noisia neurofunk reese with parallel oscillator processing, multiband distortion, and stereo width control",
                    "Build a Sleepnet heavy techno bass using analog oscillators, aggressive snapin chains, and movement automation",
                    "Create a Broken Note industrial sound with noise oscillators, distortion routing, and modular signal flow",
                    "Design a Clockvice neurohop bass using oscillator layering, creative snapin routing, and precise automation",
                    "Build a Detox Unit experimental bass with unconventional oscillator combinations and chaotic modulation matrices"
                ],
                'Vital': [
                    "Create an Alix Perez deep bass using spectral warping on sine waves with subtle harmonic enhancement",
                    "Design a Flying Lotus experimental lead using spectral effects, filter morphing, and stereo width modulation",
                    "Build a Tsuruda wonky bass with filter drive, spectral warping, and unconventional pitch modulation",
                    "Create a Mr. Carmack trap lead using saw waves with stereo spreading, filter movement, and distortion",
                    "Design a Monty future bass sound with bright wavetables, stereo modulation, and spectral processing",
                    "Build a Chris Lorenzo bassline house bass using filtered saws, punchy envelopes, and subtle distortion warmth",
                    "Create a Simula atmospheric pad using spectral warping, slow filter morphing, and wide stereo field",
                    "Design an Ihatemodels hard techno kick-bass using sine waves with spectral distortion and pitch envelope",
                    "Build a Sara Landry techno lead using spectral warping, stereo modulation, and filter drive",
                    "Create a Must Die! heavy bass using spectral effects, aggressive filtering, and movement automation",
                    "Design a Tiedye Ky melodic bass with spectral warping, filter morphing, and stereo width",
                    "Build a Lab Group experimental sound using spectral processing, LFO modulation, and filter movement",
                    "Create a Supertask neuro bass with spectral warping, precise filter automation, and stereo enhancement"
                ]
            }
        else:  # creative/abstract
            templates = {
                'Serum 2': [
                    "**Seed Exercise**: Initialize your patch. Move one parameter at a time until something makes you lean forward. Stop. What caught your attention? Follow only that feeling. | Remember: There is no wrong answer.",
                    "**Translation**: Close your eyes and feel your breath. Is it quick? Deep? Jagged? Open Serum and create a sound with that exact rhythm and texture. Let the sound breathe with you. | Stop when the energy shifts.",
                    "**Limitation**: Use only one oscillator and one filter. No effects. What can you discover in this small space? Work until you find something that surprises you. | Begin from not knowing.",
                    "**Accident**: Randomize all wavetable positions and modulation routings. Don't look at what changed. Adjust only by ear until something unexpected emerges. Trust the accident. | Follow what excites you.",
                    "**Awareness**: What's the quietest sound in your room right now? Create a patch that captures its texture, rhythm, or feeling. Not a recreation—a translation. | Work until it feels complete.",
                    "**Play**: Make a sound that would make a 4-year-old giggle. Don't overthink it. What makes your breath catch? | Time: 5 minutes or until you smile.",
                    "**Context Shift**: Design a bass sound while imagining you're underwater. How would water change the movement, the pressure, the time? Let the sound tell you what it wants to become. | Open-ended.",
                    "**Synesthesia**: What does the color purple taste like? Create that as a sound. There's no correct answer—only your answer. | Stop when the energy dissipates.",
                    "**Discovery**: Cycle through wavetables slowly. Stop when one makes you curious. Build an entire patch from that single waveform. Follow the feeling of leaning forward. | Work intuitively."
                ],
                'Phase Plant': [
                    "**Seed Exercise**: Add oscillators one at a time. After each one, listen. When something sparks excitement, stop adding. Shape only what excites you. | Remember: Follow what wants to emerge.",
                    "**Translation**: Touch the surface you're sitting on. Rough? Smooth? Cold? Warm? Create a sound with that exact texture. Let your fingers guide your ears. | Open-ended exploration.",
                    "**Limitation**: Build a complete patch using only snapin effects—no oscillators. What can effects become when they are the source? Embrace the constraint. | Trust the process.",
                    "**Accident**: Route modulation sources randomly to six different destinations. Don't undo anything. Work with what appeared. Let the accident guide you. | Stop when it feels right.",
                    "**Awareness**: Listen to the room tone around you for 30 seconds. Eyes closed. Then open Phase Plant and recreate not the sound, but the feeling of listening. | Work until the energy shifts.",
                    "**Play**: Design a sound that a plant would make if it could laugh. Completely unserious. What makes you smile while making it? | 5 minutes maximum.",
                    "**Context Shift**: Create a lead sound while pretending this is the last sound you'll ever make. What becomes important? What falls away? | Work until complete.",
                    "**Synesthesia**: What does 3 AM feel like? Not look like—feel like. Translate that feeling into modular routing and snapin chains. | Follow your intuition.",
                    "**Discovery**: Choose three random snapins. Chain them. Now find five different sounds using only those three. Notice what makes your breath catch. | Explore freely."
                ],
                'Vital': [
                    "**Seed Exercise**: Load a basic wavetable. Apply one spectral warp. If it excites you, continue. If not, try another. Stop when you lean forward. | Begin from not knowing.",
                    "**Translation**: How do shadows move across a room? Create a sound that changes at that exact pace. Let time stretch. | Work as slowly as shadows move.",
                    "**Limitation**: Use only one LFO to modulate everything. Every parameter connects to this one source. What relationships emerge? | Embrace what appears.",
                    "**Accident**: Enable spectral warping and drag the controls randomly. Don't look at the values. Adjust by feeling alone. Trust what surprises you. | Stop when it feels alive.",
                    "**Awareness**: Notice the temperature of your hands right now. Create a sound that has that exact temperature. Cold is texture. Warmth is movement. | Let the sound tell you.",
                    "**Play**: Make the sound of what purple tastes like. No overthinking. First thought, best thought. | 5 minutes of pure play.",
                    "**Context Shift**: Design a pad while imagining you're the size of an atom. How does scale change the feeling of space and time? | Work until the perspective shifts.",
                    "**Synesthesia**: What does rough tree bark sound like? Not a literal recreation—a sonic translation. Let texture become tone. | Open-ended exploration.",
                    "**Discovery**: Set a filter to self-oscillate. Now treat it as an oscillator. What happens when you flip the roles? Follow the curiosity. | Explore until complete."
                ]
            }

        content = random.choice(templates.get(synthesizer, templates['Serum 2']))
        title = f"{exercise_type.capitalize()} Sound Design Exercise"

        if exercise_type == 'technical':
            tips = [
                "Start with initializing the synth to hear your changes clearly",
                "Use your ears - trust what sounds good rather than just visual feedback",
                "Save variations as you go to compare different approaches"
            ]
        else:  # creative/abstract
            tips = [
                "There is no destination, only discovery. Follow what makes you curious",
                "If you're overthinking, you're not playing. Trust your first instinct",
                "The 'mistake' that excites you is the exercise working",
                "Stop when the energy shifts. Not everything needs finishing",
                "Your ears know more than your eyes. Close the screen if it helps",
                "If nothing excites you after 5 minutes, start completely over",
                "The exercise is in the noticing, not the result"
            ]
            tips = random.sample(tips, 3)  # Pick 3 random tips
    else:
        # AI-generated sound design prompts
        synth_info = synth_context.get(synthesizer, synth_context['Serum 2'])

        if exercise_type == 'technical':
            system_prompt = f"""You are an expert sound designer and educator specializing in {synthesizer}.
{synthesizer} is a {synth_info['type']} synthesizer with {synth_info['features']}.
It excels at {synth_info['strengths']}.

Generate a technical sound design exercise based on the signature sounds of these artists:
- Tipper, Space Laces, Virtual Riot, Resonant Language, Culprate, Chris Lorenzo
- Skrillex, Tchami, Simula, Monty, Alix Perez, Eprom, G Jones
- Koan Sound, Kursa, Seppa, Vorso, Flying Lotus, Chee, Tsuruda, Mr. Carmack
- Noisia, Sleepnet, Broken Note, Clockvice, Ihatemodels, Sara Landry
- Must Die!, Eptic, Charlesthefirst, Esseks, Tiedye Ky, Lab Group, Supertask, Detox Unit, Mr. Bill

The exercise should:
1. Reference a specific artist's signature sound style
2. Provide step-by-step technical guidance using {synthesizer}'s specific features
3. Detail synthesis parameters (oscillators, filters, modulation, effects)
4. Include tips for achieving that artist's characteristic production techniques

Keep instructions clear and actionable, referencing {synthesizer}'s actual interface elements.
Examples: "Create a Skrillex-style metallic bass", "Design a Tipper surgical bass", "Build a Virtual Riot supersized growl"."""

            user_prompt = "Create a technical sound design exercise based on one of these artists' signature sounds, with step-by-step synthesis instructions."

        else:  # creative/abstract
            system_prompt = f"""You are a creative companion for sound design. Create exercises for {synthesizer} that feel like invitations to play, not instructions to follow.

{synthesizer} is a {synth_info['type']} synthesizer with {synth_info['features']}.

Exercise Types (choose one):
- **Seed Exercise**: Finding sonic moments that spark excitement, collecting sounds that make you lean forward
- **Translation**: Translating non-sonic experiences into sound (synesthesia, textures, feelings, sensations)
- **Limitation**: Strict creative constraints that force new discoveries (one oscillator, no effects, etc.)
- **Accident**: Embracing randomness and working with unexpected results
- **Awareness**: Deep listening exercises, presence, noticing what's here now
- **Context Shift**: Changing perspective or environment (underwater, atomic scale, last sound ever, etc.)
- **Play**: Completely unserious, childlike exploration with no right answers
- **Synesthesia**: What does a color taste like? What does a texture sound like?
- **Discovery**: Exploring one element deeply, following curiosity

Format the exercise like this:
**[Exercise Type]**: [Main instruction as a question or invitation. Use short sentences. Create space for discovery.]

[Optional brief guidance in present tense]

[End with an inviting phrase]:
- "Remember: There is no wrong answer"
- "Follow what excites you"
- "Begin from not knowing"
- "Trust the accident"
- "Let the sound tell you what it wants to become"
- "Stop when the energy shifts"
- "Work until it feels complete"
- "What makes your breath catch?"

IMPORTANT:
- Remove ALL judgment language (no "good," "professional," "correct")
- Use questions more than commands
- Embrace incompleteness
- Suggest varied time frames: "5 minutes," "until you smile," "open-ended," "as slowly as shadows move"
- Focus on awareness and intuition, not technical achievement
- Create space for the user's artistic intuition to emerge
- Feel like play, not work"""

            user_prompt = "Create a creative/abstract sound design exercise that invites playful exploration and discovery. Make it feel like an invitation from a creative companion, not a technical tutorial."

        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=1.1,
                max_tokens=600,
                presence_penalty=0.9,
                frequency_penalty=0.9
            )

            content = response.choices[0].message.content.strip()

            # Extract title if present
            lines = content.split('\n')
            if lines[0].startswith('#') or (len(lines[0]) < 60 and not lines[0].endswith('.')):
                title = lines[0].replace('#', '').strip()
                content = '\n'.join(lines[1:]).strip()
            else:
                title = f"{synthesizer} - {exercise_type.capitalize()} Exercise"

            # Extract tips
            tips = []
            tip_section_match = re.search(r'\*\*Tips.*?\*\*:?\s*\n(.*?)(?=\n\n|\Z)', content, re.DOTALL | re.IGNORECASE)
            if tip_section_match:
                tip_section = tip_section_match.group(1)
                for line in tip_section.split('\n'):
                    line = line.strip()
                    if line.startswith('-') or line.startswith('•') or line.startswith('*'):
                        tip = re.sub(r'^[-•*]\s*', '', line).strip()
                        if tip and len(tip) > 10:
                            tips.append(tip)
                content = re.sub(r'\*\*Tips.*?\*\*:?\s*\n.*?(?=\n\n|\Z)', '', content, flags=re.DOTALL | re.IGNORECASE).strip()

            if not tips:
                if exercise_type == 'technical':
                    tips = [
                        "Reference tracks can help guide your sound design decisions",
                        "A/B test your patch in a mix context, not just solo",
                        "Document your process - you'll learn patterns in your workflow"
                    ]
                else:  # creative/abstract
                    tips = [
                        "There is no destination, only discovery. Follow what makes you curious",
                        "If you're overthinking, you're not playing. Trust your first instinct",
                        "The 'mistake' that excites you is the exercise working",
                        "Stop when the energy shifts. Not everything needs finishing",
                        "Your ears know more than your eyes. Close the screen if it helps",
                        "If nothing excites you after 5 minutes, start completely over",
                        "The exercise is in the noticing, not the result"
                    ]
                    tips = random.sample(tips, 3)

        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            # Fallback to template
            content = random.choice(templates.get(synthesizer, templates['Serum 2']))
            title = f"{synthesizer} - {exercise_type.capitalize()} Exercise"
            tips = ["Experiment with modulation sources", "Layer multiple oscillators", "Use effects creatively"]

    # Determine difficulty and estimated time (matched pairs)
    difficulty_time_pairs = [
        ('Beginner', '15 minutes'),
        ('Intermediate', '30 minutes'),
        ('Expert', '45 minutes')
    ]

    difficulty, estimated_time = random.choice(difficulty_time_pairs)

    return {
        'title': title,
        'content': content,
        'synthesizer': synthesizer,
        'exerciseType': exercise_type,
        'difficulty': difficulty,
        'estimatedTime': estimated_time,
        'tips': tips[:3],
        'timestamp': datetime.utcnow().isoformat()
    }

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    with tracer.start_as_current_span("health-check"):
        try:
            redis_client.ping()
            return jsonify({'status': 'healthy', 'service': 'prompt-generator'}), 200
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return jsonify({'status': 'unhealthy', 'error': str(e)}), 503

@app.route('/generate', methods=['POST'])
def generate():
    """Generate a writing prompt based on selected genres"""
    with tracer.start_as_current_span("generate-prompt") as span:
        try:
            data = request.json
            genres = data.get('genres', [])
            user_id = data.get('userId', 'anonymous')
            
            span.set_attribute("user.id", user_id)
            span.set_attribute("genres.count", len(genres))
            span.set_attribute("genres.list", ','.join(genres))
            
            if not genres:
                return jsonify({'error': 'At least one genre must be selected'}), 400
            
            # Generate cache key
            
            # Generate new prompt
            span.add_event("generating-new-prompt")
            
            if USE_AI:
                prompt = generate_prompt_with_ai(genres)
            else:
                prompt = generate_prompt_from_template(genres)
            
            
            # Track metrics
            span.set_attribute("prompt.title", prompt['title'])
            span.set_attribute("prompt.difficulty", prompt['difficulty'])
            span.set_attribute("prompt.word_count", prompt['wordCount'])
            
            return jsonify(prompt), 200
            
        except Exception as e:
            span.record_exception(e)
            span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
            logger.error(f"Prompt generation failed: {str(e)}")
            return jsonify({'error': 'Failed to generate prompt'}), 500

@app.route('/feedback', methods=['POST'])
def feedback():
    """Collect feedback on generated prompts"""
    with tracer.start_as_current_span("prompt-feedback") as span:
        try:
            data = request.json
            prompt_id = data.get('promptId')
            rating = data.get('rating')
            user_id = data.get('userId', 'anonymous')

            span.set_attribute("user.id", user_id)
            span.set_attribute("prompt.id", prompt_id)
            span.set_attribute("feedback.rating", rating)

            # Store feedback in Redis
            feedback_key = f"feedback:{prompt_id}:{user_id}"
            redis_client.setex(
                feedback_key,
                86400 * 30,  # 30 days TTL
                json.dumps({
                    'rating': rating,
                    'timestamp': datetime.utcnow().isoformat()
                })
            )

            return jsonify({'status': 'success'}), 200

        except Exception as e:
            span.record_exception(e)
            logger.error(f"Feedback submission failed: {str(e)}")
            return jsonify({'error': 'Failed to submit feedback'}), 500

@app.route('/generate-sound-design', methods=['POST'])
def generate_sound_design():
    """Generate a sound design exercise based on synthesizer and exercise type"""
    with tracer.start_as_current_span("generate-sound-design") as span:
        try:
            data = request.json
            synthesizer = data.get('synthesizer', 'Serum 2')
            exercise_type = data.get('exerciseType', 'technical')
            user_id = data.get('userId', 'anonymous')

            span.set_attribute("user.id", user_id)
            span.set_attribute("synthesizer", synthesizer)
            span.set_attribute("exercise.type", exercise_type)

            # Validate inputs
            valid_synths = ['Serum 2', 'Phase Plant', 'Vital']
            valid_types = ['technical', 'creative']

            if synthesizer not in valid_synths:
                return jsonify({'error': f'Invalid synthesizer. Must be one of: {", ".join(valid_synths)}'}), 400

            if exercise_type not in valid_types:
                return jsonify({'error': f'Invalid exercise type. Must be one of: {", ".join(valid_types)}'}), 400

            # Generate prompt
            span.add_event("generating-sound-design-prompt")
            prompt = generate_sound_design_prompt(synthesizer, exercise_type)

            # Track metrics
            span.set_attribute("prompt.title", prompt['title'])
            span.set_attribute("prompt.difficulty", prompt['difficulty'])
            span.set_attribute("prompt.estimated_time", prompt['estimatedTime'])

            return jsonify(prompt), 200

        except Exception as e:
            span.record_exception(e)
            span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
            logger.error(f"Sound design prompt generation failed: {str(e)}")
            return jsonify({'error': 'Failed to generate sound design prompt'}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=os.getenv('FLASK_ENV') == 'development')