import os
import logging
from typing import List, Optional
from huggingface_hub import InferenceClient
# Setup logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class ContentEngine:
    """
    Engine to generate LinkedIn post text and corresponding images
    using Google GenAI and Hugging Face FLUX.
    """
    def __init__(self, gemini_api_key: Optional[str] = None, hf_token: Optional[str] = None):
        self.gemini_api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
        self.hf_token = hf_token or os.getenv("HF_TOKEN")
        self.use_gemini = False
        self.use_flux = False
        self.client = None
        self.hf_client = None
        
        # Initialize Google GenAI Client if API key is provided
        if self.gemini_api_key:
            try:
                from google import genai
                # Initialize standard GenAI Client
                self.client = genai.Client(api_key=self.gemini_api_key)
                self.use_gemini = True
                logger.info("ContentEngine: Google GenAI Client initialized successfully.")
            except Exception as e:
                logger.error(f"Failed to initialize Google GenAI Client: {e}")

        # Initialize Hugging Face Inference Client if token is provided
        if self.hf_token:
            try:
                # Remove quotes if they exist around the token (sometimes added in .env)
                clean_token = self.hf_token.strip("'\"")
                self.hf_client = InferenceClient(
                    token=clean_token
                )
                self.use_flux = True
                logger.info("ContentEngine: Hugging Face Inference Client initialized successfully.")
            except Exception as e:
                logger.error(f"Failed to initialize Hugging Face Inference Client: {e}")

        if not self.use_gemini:
            logger.warning("ContentEngine initialized without GEMINI_API_KEY. Fallback mock text will be used.")

    def generate_post_text(self, topic: str, tone: str = "professional", keywords: Optional[List[str]] = None) -> str:
        """
        Generates structured text for a LinkedIn post based on topic, tone, and optional keywords
        using the Gemini 3.5 Flash model.
        """
        kw_str = ", ".join(keywords) if keywords else "None"
        
        prompt = (
            f"You are an expert LinkedIn content creator and personal branding strategist.\n"
            f"Write a highly engaging LinkedIn post about: '{topic}'.\n"
            f"Tone: {tone}\n"
            f"Keywords to include: {kw_str}\n\n"
            f"Requirements:\n"
            f"1. Start the post with a highly relevant emoji or icon that matches the topic and emotional tone. Choose naturally from emojis such as: 🤖 (AI), 📊 (Data Science), 🚀 (Innovation), 💡 (Ideas & Learning), 🔥 (Trending Topics), 🎯 (Career Growth), ⚙️ (Automation), 💻 (Software Development), 🧠 (Machine Learning), 📈 (Business Growth), 🌐 (Technology), 🔍 (Insights), 🏆 (Success), 🎓 (Education), 🛠️ (Engineering), ☁️ (Cloud Computing), 🤝 (Collaboration), 📱 (Digital Transformation), 🔮 (Future Trends), 🌟 (Achievements), 🚦 (Decision Making), 🗺️ (Strategy), 🏗️ (Building Products), 🧪 (Experimentation), ⚡ (Productivity), 🌍 (Global Impact), 🛡️ (Cybersecurity), 💼 (Professional Development), 📚 (Knowledge Sharing), or other contextually appropriate symbols.\n"
            f"2 Follow the emoji with a powerful, curiosity-driven hook in the first 1-2 lines that immediately captures attention and encourages users to click 'see more'. The opening should feel professional, insightful, and engaging. Use one of these hook styles:\n"
            f"3. Use short, readable paragraphs (1-3 sentences each) with bullet points where appropriate.\n"
            f"4. Include a clear call-to-action (CTA) at the end encouraging comments/discussion.\n"
            f"5. Add 3-5 highly relevant hashtags at the very bottom.\n"
            f"6. Do NOT use emojis excessively, but keep it visually spaced and inviting.\n"
            f"7. Avoid generic openings such as 'The future is here' or 'In today's world'. Make every opening unique, scroll-stopping, and LinkedIn-worthy.\n"
        )

        if self.use_gemini and self.client:
            try:
                response = self.client.models.generate_content(
                    model="gemini-3.5-flash",
                    contents=prompt
                )
                return response.text.strip()
            except Exception as e:
                logger.error(f"Gemini post generation failed: {e}. Falling back to Hugging Face...")
                
        # Fallback to Hugging Face text generation
        if self.use_flux and self.hf_client:
            try:
                logger.info("Attempting to generate post text using Hugging Face Llama...")
                messages = [{"role": "user", "content": prompt}]
                response = self.hf_client.chat_completion(
                    model="meta-llama/Llama-3.3-70B-Instruct",
                    messages=messages,
                    max_tokens=600
                )
                content = response.choices[0].message.content.strip()
                if content:
                    return content
            except Exception as hf_err:
                logger.error(f"Hugging Face post generation failed: {hf_err}")
                
        # Fallback Mock post generation
        return self._generate_mock_post(topic, tone, keywords)

    def generate_image_prompt(self, post_text: str) -> str:
        """
        Analyzes the generated post text and creates a detailed image generation prompt
        suitable for Imagen using the Gemini 3.5 Flash model, enforcing strict guidelines.
        """
        prompt = (
            f"You are a world-class Creative Director, LinkedIn Visual Designer, and AI Art Director. "
            f"Analyze the following LinkedIn post and generate a highly detailed, professional image generation prompt for Google Imagen 4.\n\n"

            f"LinkedIn Post:\n{post_text}\n\n"

            f"Your task is to first understand the post and identify:\n"
            f"- Main topic\n"
            f"- Industry/domain\n"
            f"- Key concepts\n"
            f"- Important visual objects\n"
            f"- Human activities\n"
            f"- Emotional tone\n"
            f"- Transformation, outcome, or message\n\n"

            f"Then generate a single high-quality image prompt that visually communicates the post content without using text.\n\n"

            f"1. PRIMARY OBJECTIVE:\n"
            f"The generated image must tell the story of the LinkedIn post visually. "
            f"A viewer should immediately understand the core message, industry, goal, and idea without reading any text.\n\n"

            f"2. VISUAL STORYTELLING:\n"
            f"Create a rich visual scene using people, environments, actions, technology, workflows, objects, symbols, concepts, and storytelling elements. "
            f"The image should feel meaningful rather than decorative.\n\n"

            f"3. VISUAL ELEMENTS:\n"
            f"Use relevant elements whenever applicable, such as:\n"
            f"- Professionals and teams\n"
            f"- AI systems and intelligent agents\n"
            f"- Dashboards and analytics\n"
            f"- Data pipelines and workflows\n"
            f"- Interactive charts and visualizations\n"
            f"- Career growth and learning journeys\n"
            f"- Interviews and workplace collaboration\n"
            f"- Travel planning systems and maps\n"
            f"- Automation systems and software platforms\n"
            f"- Laptops, mobile devices, digital interfaces\n"
            f"- Modern office or futuristic environments\n\n"

            f"4. VISUAL NARRATIVE:\n"
            f"Whenever possible, represent one of the following transformations:\n"
            f"- Problem to Solution\n"
            f"- Learning to Growth\n"
            f"- Beginner to Expert\n"
            f"- Manual Process to Automation\n"
            f"- Idea to Execution\n"
            f"- Challenge to Success\n\n"

            f"5. STYLE SELECTION:\n"
            f"Automatically choose the most suitable artistic style based on the post topic:\n"
            f"- Cinematic Digital Art\n"
            f"- Realistic Photography\n"
            f"- 3D Illustration\n"
            f"- Isometric Design\n"
            f"- Modern Infographic Style\n"
            f"- Futuristic AI Artwork\n"
            f"- Professional Animated Artwork\n"
            f"- Corporate LinkedIn Visual Design\n\n"

            f"6. BACKGROUND REQUIREMENTS:\n"
            f"Generate a visually rich and topic-relevant background.\n"
            f"For AI topics use neural networks, intelligent systems, holographic interfaces, and data flows.\n"
            f"For Data Science topics use dashboards, analytics, predictive models, charts, and pipelines.\n"
            f"For Career topics use offices, recruiters, interviews, and professional growth environments.\n"
            f"For Travel AI topics use airports, destinations, hotels, interactive maps, travel dashboards, and multi-agent workflows.\n"
            f"For Automation topics use connected systems, workflows, integrations, APIs, and productivity environments.\n\n"

            f"7. CREATIVE ENHANCEMENTS:\n"
            f"Use modern visual storytelling techniques including:\n"
            f"- Dynamic compositions\n"
            f"- Depth and perspective\n"
            f"- Futuristic UI overlays\n"
            f"- Glassmorphism\n"
            f"- Soft ambient lighting\n"
            f"- Volumetric lighting\n"
            f"- Motion and action elements\n"
            f"- Visual metaphors\n"
            f"- Layered information design\n\n"

            f"8. IMAGE QUALITY:\n"
            f"Generate a premium LinkedIn-ready image.\n"
            f"The image must be:\n"
            f"- High Resolution\n"
            f"- Professional\n"
            f"- Modern\n"
            f"- Highly Detailed\n"
            f"- Visually Engaging\n"
            f"- Balanced Composition\n"
            f"- Strong Focal Point\n"
            f"- Social Media Ready\n\n"

            f"9. VARIETY REQUIREMENT:\n"
            f"Avoid generating the same style repeatedly. "
            f"Use different combinations of environments, backgrounds, compositions, visual metaphors, objects, icons, graphics, illustrations, and character arrangements so each generated image feels unique and directly related to the specific post.\n\n"

            f"10. STRICT NEGATIVE INSTRUCTIONS:\n"
            f"Do NOT include any text, headlines, captions, words, letters, logos, watermarks, labels, social media templates, title cards, banners, posters, read-more text, placeholder text, UI mockup text, or empty decorative layouts. "
            f"The image must communicate entirely through visuals.\n\n"

            f"11. OUTPUT REQUIREMENT:\n"
            f"Return ONLY the final detailed image generation prompt. "
            f"Do not explain your reasoning. "
            f"Do not use markdown. "
            f"Do not add quotes. "
            f"Output only the final image prompt."
            )

        if self.use_gemini and self.client:
            try:
                response = self.client.models.generate_content(
                    model="gemini-3.5-flash",
                    contents=prompt
                )
                return response.text.strip()
            except Exception as e:
                logger.error(f"Gemini image prompt generation failed: {e}. Falling back to Hugging Face...")

        # Fallback to Hugging Face text generation for the image prompt
        if self.use_flux and self.hf_client:
            try:
                logger.info("Attempting to generate image prompt using Hugging Face Llama...")
                messages = [{"role": "user", "content": prompt}]
                response = self.hf_client.chat_completion(
                    model="meta-llama/Llama-3.3-70B-Instruct",
                    messages=messages,
                    max_tokens=300
                )
                content = response.choices[0].message.content.strip()
                if content:
                    return content
            except Exception as hf_err:
                logger.error(f"Hugging Face image prompt generation failed: {hf_err}")

        # Fallback Mock image prompt
        return f"A modern corporate vector illustration showing a clean workspace with digital elements representing collaboration and growth, soft blue and teal palette, minimalist background."

    def generate_image_with_gemini(self, prompt: str, output_path: str = "generated_gemini_image.png") -> Optional[str]:
        """
        Generates an image using Google's Imagen 4 model via the GenAI Client and saves it locally.
        """
        if not self.use_gemini or not self.client:
            logger.warning("Gemini Image Generation: Client not initialized or API Key missing. Skipping.")
            return None

        try:
            try:
                from google.genai import types
            except Exception:
                types = None

            logger.info("Requesting image from Google Imagen 4 (imagen-4.0-generate-001)...")

            if types is not None:
                config = types.GenerateImagesConfig(
                    number_of_images=1,
                    aspect_ratio="16:9",  # Landscape fits LinkedIn feed perfectly
                    output_mime_type="image/png"
                )
            else:
                # Fallback plain dict for environments without google.genai types available
                config = {
                    "number_of_images": 1,
                    "aspect_ratio": "16:9",
                    "output_mime_type": "image/png",
                }

            response = self.client.models.generate_images(
                model="imagen-4.0-generate-001",
                prompt=prompt,
                config=config
            )
            
            if response.generated_images:
                # The modern SDK returns PIL Image objects directly inside the response
                generated_image = response.generated_images[0]
                generated_image.image.save(output_path)
                logger.info(f"Gemini Imagen image successfully saved to: {output_path}")
                return output_path
            else:
                logger.error("No images returned from Google Imagen API.")
                return None
        except Exception as e:
            logger.error(f"Google Imagen generation failed: {e}")
            return None

    def generate_image_with_flux(self, prompt: str, output_path: str = "generated_flux_image.png") -> Optional[str]:
        """
        Generates an image using Hugging Face's FLUX.1-schnell model via InferenceClient and saves it locally.
        """
        if not self.use_flux or not self.hf_client:
            logger.warning("FLUX Image Generation: Client not initialized or HF_TOKEN missing. Skipping.")
            return None

        try:
            logger.info("Requesting image from Hugging Face FLUX.1-schnell...")
            # We want LinkedIn quality landscape image, e.g. width=1024, height=576
            image = self.hf_client.text_to_image(prompt, model="black-forest-labs/FLUX.1-schnell", width=1024, height=576)
            
            # Ensure output directory exists
            out_dir = os.path.dirname(output_path)
            if out_dir:
                os.makedirs(out_dir, exist_ok=True)
                
            image.save(output_path)
            logger.info(f"FLUX image successfully saved to: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Hugging Face FLUX generation failed: {e}")
            return None

    def generate_topic(self) -> str:
        """
        Generates a trending, engaging, and professional LinkedIn post topic related to
        AI, Machine Learning, Data Science, Software Engineering, Automation, Career Growth,
        Startups, Productivity, Technology Trends, LLMs, Agents, or Emerging Technologies.
        Uses Gemini first, falling back to Hugging Face Llama.
        """
        prompt = (
            "You are a thought leader, social media strategist, and creative content director.\n"
            "Generate a single highly engaging, professional, and trending LinkedIn post topic.\n"
            "The topic must be relevant to one of these fields: AI, Machine Learning, Data Science, "
            "Software Engineering, Automation, Career Growth, Startups, Productivity, Technology Trends, "
            "LLMs, Agents, or Emerging Technologies.\n\n"
            "Requirements:\n"
            "1. Output ONLY the topic title. Do not add quotes, intro text, metadata, or extra explanation.\n"
            "2. Make it punchy, thought-provoking, and tailored to business/tech professionals on LinkedIn.\n"
            "3. Make it unique (e.g. 'The shift from prompt engineering to agentic orchestration', "
            "'How junior developers can leverage AI to level up fast', 'The hidden cost of microservice complexity').\n"
            "4. Do NOT output markdown formatting."
        )

        if self.use_gemini and self.client:
            try:
                response = self.client.models.generate_content(
                    model="gemini-3.5-flash",
                    contents=prompt
                )
                topic = response.text.strip()
                if topic:
                    return topic
            except Exception as e:
                logger.error(f"Gemini topic generation failed: {e}. Falling back to Hugging Face...")

        # Fallback to Hugging Face text generation
        if self.use_flux and self.hf_client:
            try:
                logger.info("Attempting to generate topic using Hugging Face Llama...")
                messages = [{"role": "user", "content": prompt}]
                response = self.hf_client.chat_completion(
                    model="meta-llama/Llama-3.3-70B-Instruct",
                    messages=messages,
                    max_tokens=60
                )
                topic = response.choices[0].message.content.strip()
                # Clean up quotes if returned by the LLM
                topic = topic.strip("'\"")
                if topic:
                    return topic
            except Exception as hf_err:
                logger.error(f"Hugging Face topic generation failed: {hf_err}")

        # Fallback Mock topics in case both fail
        import random
        mock_topics = [
            "How AI Agents are redefining enterprise software architecture",
            "Why the future of software engineering lies in multi-agent orchestration",
            "The evolution from Retrieval-Augmented Generation (RAG) to Agentic Workflows",
            "How to build a personal brand in the age of AI automation",
            "Key strategies for junior developers navigating the AI revolution"
        ]
        return random.choice(mock_topics)

    def _generate_mock_post(self, topic: str, tone: str, keywords: Optional[List[str]]) -> str:
        """Fallback mock post generator when no API key is present."""
        kw_tags = " ".join([f"#{kw.replace(' ', '')}" for kw in (keywords or [])])
        return (
            f"🚀 [HOOK] Want to master {topic}? Here's the key truth.\n\n"
            f"Many professionals struggle with this, but keeping it simple is key. "
            f"By focusing on core principles, you can drive significant impact in your daily work.\n\n"
            f"Key Takeaways:\n"
            f"• Consistency beats intensity\n"
            f"• Focus on value creation\n"
            f"• Never stop learning\n\n"
            f"What's your biggest challenge when dealing with {topic}? Let's discuss in the comments! 👇\n\n"
            f"#ProfessionalDevelopment #{topic.replace(' ', '')} {kw_tags}"
        )
