from flask import Flask, request, jsonify
from flask_cors import CORS
import redis
import json
import random
import hashlib
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
    """Randomly select word count and corresponding difficulty"""
    options = [
        (250, 'Very Easy'),
        (500, 'Easy'),
        (750, 'Medium'),
        (1000, 'Hard')
    ]
    word_count, difficulty = random.choice(options)
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

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=os.getenv('FLASK_ENV') == 'development')