import os
import sys
import socket
# Set global socket timeout to 15 seconds to prevent hanging API requests
socket.setdefaulttimeout(15.0)

import argparse
import logging
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont

# Import our custom modules
from content_engine import ContentEngine
from social_api import LinkedInAPI

# Setup logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def safe_print(text: str) -> None:
    """Prints text to standard output, handling Windows terminal encoding limitations gracefully."""
    try:
        print(text)
    except UnicodeEncodeError:
        if hasattr(sys.stdout, 'buffer'):
            try:
                sys.stdout.buffer.write((str(text) + '\n').encode('utf-8', errors='replace'))
                sys.stdout.flush()
            except Exception:
                print(str(text).encode('ascii', errors='replace').decode('ascii'))
        else:
            print(str(text).encode('ascii', errors='replace').decode('ascii'))

def generate_pillow_banner(title: str, subtitle: str, output_path: str = "generated_post_visual.png") -> str:
    """
    Generates a premium, text-free modern tech 3D vector illustration using Pillow.
    Features 3D cylinders for database/destination, glowing streams, and orbital rings.
    """
    logger.info("Generating premium 3D tech graphic using Pillow...")
    
    # Standard LinkedIn post image dimensions (1.91:1 aspect ratio)
    width, height = 1200, 628
    
    # Create base RGBA image for transparency/layer support
    image = Image.new("RGBA", (width, height))
    draw = ImageDraw.Draw(image)
    
    # 1. Slate-to-Indigo background gradient
    for y in range(height):
        r = int(15 + (10 - 15) * (y / height))
        g = int(23 + (15 - 23) * (y / height))
        b = int(42 + (30 - 42) * (y / height))
        draw.line([(0, y), (width, y)], fill=(r, g, b, 255))
        
    # Create an overlay layer for transparent/glowing layers
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    
    # 2. Draw modern background glow circles
    overlay_draw.ellipse([(-150, -150), (450, 450)], fill=(45, 212, 191, 20)) # Teal glow left
    overlay_draw.ellipse([(800, 250), (1350, 800)], fill=(99, 102, 241, 25)) # Indigo glow right
    
    # 3. Draw perspective ground lines (3D depth grid)
    horizon_y = 150
    # Converging lines
    for x_start in range(-400, width + 400, 100):
        overlay_draw.line([(width // 2, horizon_y), (x_start, height)], fill=(99, 102, 241, 15), width=1)
    # Horizontal grid lines with progressive spacing
    current_y = horizon_y
    step = 10
    while current_y < height:
        overlay_draw.line([(0, int(current_y)), (width, int(current_y))], fill=(99, 102, 241, 20), width=1)
        step *= 1.35
        current_y += step

    # Helper function to draw a sleek 3D cylinder
    def draw_3d_cylinder(od, cx, cy, w, h, thickness, base_color, top_color, outline_color):
        # Bottom face shadow
        od.ellipse([cx - w/2, cy - h/2 + thickness, cx + w/2, cy + h/2 + thickness], fill=(0, 0, 0, 60))
        # Cylinder side wall
        od.rectangle([cx - w/2, cy, cx + w/2, cy + thickness], fill=base_color)
        od.ellipse([cx - w/2, cy - h/2 + thickness, cx + w/2, cy + h/2 + thickness], fill=base_color, outline=outline_color, width=1)
        # Cylinder top face
        od.ellipse([cx - w/2, cy - h/2, cx + w/2, cy + h/2], fill=top_color, outline=outline_color, width=2)

    # 4. Draw Google Sheets Database Stack (Left)
    db_x = 250
    db_base_y = 400
    db_w = 160
    db_h = 45
    db_thick = 35
    db_gap = 48
    # Stack of 3 database disks
    for i in range(3):
        cy = db_base_y - (i * db_gap)
        draw_3d_cylinder(
            overlay_draw, db_x, cy, db_w, db_h, db_thick,
            base_color=(13, 148, 136, 255), # Dark teal
            top_color=(20, 184, 166, 255),  # Bright teal
            outline_color=(45, 212, 191, 255) # Light teal border
        )

    # 5. Draw Social Destination Stacks (Right)
    dest_x = 950
    dest1_y = 220
    dest2_y = 440
    dest_w = 120
    dest_h = 35
    dest_thick = 25
    dest_gap = 35
    
    # Destination Stack 1 (Top Right)
    for i in range(3):
        cy = dest1_y - (i * dest_gap)
        draw_3d_cylinder(
            overlay_draw, dest_x, cy, dest_w, dest_h, dest_thick,
            base_color=(79, 70, 229, 255), # Dark indigo
            top_color=(99, 102, 241, 255),  # Indigo
            outline_color=(129, 140, 248, 255) # Light indigo border
        )

    # Destination Stack 2 (Bottom Right)
    for i in range(3):
        cy = dest2_y - (i * dest_gap)
        draw_3d_cylinder(
            overlay_draw, dest_x, cy, dest_w, dest_h, dest_thick,
            base_color=(219, 39, 119, 255), # Dark pink/magenta
            top_color=(236, 72, 153, 255),  # Magenta
            outline_color=(244, 114, 182, 255) # Light pink border
        )

    # 6. Draw central processor node (Center)
    center_x = 600
    center_y = 314
    # Concentric orbital rings around center
    overlay_draw.ellipse([center_x - 180, center_y - 80, center_x + 180, center_y + 80], outline=(99, 102, 241, 80), width=2)
    overlay_draw.ellipse([center_x - 120, center_y - 50, center_x + 120, center_y + 50], outline=(45, 212, 191, 90), width=1)
    
    # Glowing center sphere
    overlay_draw.ellipse([center_x - 45, center_y - 45, center_x + 45, center_y + 45], fill=(15, 23, 42, 240), outline=(99, 102, 241, 255), width=3)
    overlay_draw.ellipse([center_x - 30, center_y - 30, center_x + 30, center_y + 30], fill=(99, 102, 241, 150))
    overlay_draw.ellipse([center_x - 12, center_y - 12, center_x + 12, center_y + 12], fill=(255, 255, 255, 255))

    # 7. Draw data stream pipelines
    # From DB to Center
    overlay_draw.line([(db_x + 80, db_base_y - 50), (center_x - 120, center_y)], fill=(45, 212, 191, 180), width=5)
    overlay_draw.line([(db_x + 80, db_base_y - 50), (center_x - 120, center_y)], fill=(255, 255, 255, 255), width=2)
    
    # From Center to Destination 1
    overlay_draw.line([(center_x + 120, center_y), (dest_x - 60, dest1_y - 30)], fill=(99, 102, 241, 180), width=4)
    # From Center to Destination 2
    overlay_draw.line([(center_x + 120, center_y), (dest_x - 60, dest2_y - 30)], fill=(236, 72, 153, 180), width=4)
    
    # 8. Draw floating data particles along the lines
    particles = [
        (380, 320, 10, (45, 212, 191, 255)),
        (460, 316, 7, (255, 255, 255, 255)),
        (720, 275, 8, (99, 102, 241, 255)),
        (780, 260, 6, (255, 255, 255, 255)),
        (740, 350, 9, (236, 72, 153, 255)),
        (830, 380, 7, (255, 255, 255, 255))
    ]
    for px, py, r, pcol in particles:
        # Outer glow
        overlay_draw.ellipse([px - r - 4, py - r - 4, px + r + 4, py + r + 4], fill=(pcol[0], pcol[1], pcol[2], 80))
        # Core
        overlay_draw.ellipse([px - r, py - r, px + r, py + r], fill=pcol)

    # Composite overlay onto base image
    final_image = Image.alpha_composite(image, overlay)
    
    # Convert back to RGB for saving
    rgb_image = final_image.convert("RGB")
    rgb_image.save(output_path)
    logger.info(f"Visual banner saved at: {output_path}")
    return output_path

def main():
    # Load environment variables from .env file
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="LinkedIn Automation Agent - Orchestrator")
    
    # Content inputs
    parser.add_argument(
        "--topic", 
        type=str, 
        default=None, 
        help="The primary subject/topic for the LinkedIn post. If omitted, a topic will be automatically generated using AI."
    )
    parser.add_argument(
        "--tone", 
        type=str, 
        default="professional", 
        help="The tone of the post (e.g., professional, casual, thought-provoking, energetic)."
    )
    parser.add_argument(
        "--keywords", 
        type=str, 
        help="Comma-separated keywords to inject into the post."
    )
    
    # Visual options
    parser.add_argument(
        "--no-image", 
        dest="generate_image",
        action="store_false", 
        help="Disable automatic visual banner generation (enabled by default)."
    )
    parser.set_defaults(generate_image=True)
    parser.add_argument(
        "--image-engine",
        type=str,
        choices=["pillow", "gemini", "flux"],
        default="flux",
        help="The engine to use for image generation (choices: pillow, gemini, flux; default: flux)."
    )
    parser.add_argument(
        "--banner-subtitle", 
        type=str, 
        default="Read the full post below", 
        help="Subtitle text to display on the generated image banner (only used with --image-engine pillow)."
    )
    
    # Publishing behavior
    parser.add_argument(
        "--draft", 
        action="store_true", 
        default=False, 
        help="Run in dry-run/draft mode (does not post to LinkedIn). Disabled by default."
    )
    parser.add_argument(
        "--publish", 
        dest="draft", 
        action="store_false", 
        help="Publish the generated post directly to LinkedIn (default behavior)."
    )

    args = parser.parse_args()
    
    keywords_list = [k.strip() for k in args.keywords.split(",")] if args.keywords else None
    
    logger.info(f"Starting LinkedIn Automation Agent...")
    
    # 1. Content Generation
    engine = ContentEngine()
    
    topic = args.topic
    if not topic:
        logger.info("No topic supplied. Generating topic using AI...")
        topic = engine.generate_topic()
        
    logger.info(f"Target Topic: '{topic}'")
    logger.info(f"Tone: '{args.tone}' | Keywords: {keywords_list}")
    
    post_text = engine.generate_post_text(
        topic=topic, 
        tone=args.tone, 
        keywords=keywords_list
    )
    
    image_prompt = engine.generate_image_prompt(post_text)
    
    safe_print("\n" + "="*50)
    safe_print(" GENERATED POST TEXT (Length: {} chars)".format(len(post_text)))
    safe_print("="*50)
    safe_print(post_text)
    safe_print("="*50)
    
    safe_print("\n" + "="*50)
    safe_print(" GENERATED IMAGE PROMPT FOR DALL-E / MIDJOURNEY")
    safe_print("="*50)
    safe_print(image_prompt)
    safe_print("="*50 + "\n")
    
    # 2. Image Generation
    image_path = None
    if args.generate_image:
        if args.image_engine == "flux":
            logger.info("Attempting to generate image using Hugging Face FLUX...")
            image_path = engine.generate_image_with_flux(image_prompt, "generated_flux_image.png")
            if not image_path:
                logger.warning("FLUX image generation failed. Falling back to Pillow banner...")
                image_path = generate_pillow_banner(
                    title=topic,
                    subtitle=args.banner_subtitle,
                    output_path="generated_post_visual.png"
                )
        elif args.image_engine == "gemini":
            logger.info("Attempting to generate image using Google Gemini (Imagen 3)...")
            image_path = engine.generate_image_with_gemini(image_prompt, "generated_gemini_image.png")
            if not image_path:
                logger.warning("Gemini image generation failed or was skipped. Falling back to Pillow banner...")
                image_path = generate_pillow_banner(
                    title=topic,
                    subtitle=args.banner_subtitle,
                    output_path="generated_post_visual.png"
                )
        else:  # pillow
            image_path = generate_pillow_banner(
                title=topic,
                subtitle=args.banner_subtitle,
                output_path="generated_post_visual.png"
            )
            
        if image_path:
            safe_print(f"Generated post image saved to: {os.path.abspath(image_path)}\n")

    # 3. Social Integration (LinkedIn API)
    post_url = None
    if args.draft:
        logger.info("Agent is running in DRAFT mode. Skipping LinkedIn API upload.")
        logger.info("To publish this post, rerun with the '--publish' flag.")
        post_url = "Draft (Not Published)"
    else:
        # Check access token
        access_token = os.getenv("LINKEDIN_ACCESS_TOKEN")
        if not access_token or "your_linkedin_access_token_here" in access_token:
            logger.error(
                "Cannot publish post: LINKEDIN_ACCESS_TOKEN is missing or contains template placeholder. "
                "Please configure it in your .env file."
            )
            post_url = "Skipped (Missing Token)"
        else:
            api = LinkedInAPI(access_token=access_token)
            try:
                if image_path:
                    logger.info("Publishing post with image...")
                    result = api.post_with_image(
                        text=post_text, 
                        image_path=image_path, 
                        image_title=topic
                    )
                else:
                    logger.info("Publishing text-only post...")
                    result = api.post_text(text=post_text)
                    
                logger.info("Publish action complete!")
                safe_print("\nLinkedIn API Response:")
                safe_print(result)
                
                # Extract post URN to construct LinkedIn URL
                if isinstance(result, dict) and "id" in result:
                    post_urn = result["id"]
                    post_url = f"https://www.linkedin.com/feed/update/{post_urn}"
                else:
                    post_url = "Published (URL unavailable)"
                
            except Exception as e:
                logger.error(f"Failed to publish to LinkedIn: {e}")
                post_url = f"Failed to Publish: {e}"

    # 4. Google Sheets Logging
    logger.info("Logging generated post to Google Sheets...")
    try:
        from sheets_logger import append_post_to_sheet
        from datetime import datetime
        import json
        
        current_date = datetime.now().strftime("%Y-%m-%d")
        sheet_id = os.getenv("GOOGLE_SHEET_ID", "17W1Z6LfM0EWue2U9burrkCeBpWWN7K90U1V0FAOSyyw")
        
        image_val = os.path.abspath(image_path) if image_path else None
        
        sheet_result = append_post_to_sheet(
            sheet_id=sheet_id,
            date_str=current_date,
            topic=topic,
            image_path_or_url=image_val,
            content=post_text,
            post_url=post_url
        )
        safe_print("\n" + "="*50)
        safe_print(" GOOGLE SHEET LOGGING SUCCESS")
        safe_print("="*50)
        safe_print(json.dumps(sheet_result, indent=2))
        safe_print("="*50 + "\n")
    except Exception as e:
        logger.error(f"Failed to log post to Google Sheets: {e}")

if __name__ == "__main__":
    
    main()
