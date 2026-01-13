"""Main entry point for the learning material generation pipeline."""

import argparse
import sys
from pathlib import Path
from typing import Optional, Callable

from utils.input_handler import InputHandler
from agents.orchestrator import Orchestrator
from converters.docusaurus_converter import DocusaurusConverter


def progress_callback(message: str) -> None:
    """Default progress callback that prints to console."""
    print(f"[PROGRESS] {message}")


def main():
    """Main function to run the pipeline."""
    parser = argparse.ArgumentParser(
        description="Generate learning materials using AI agents and STORM"
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to input JSON file with topic, bahasa, and audience"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="output",
        help="Output directory (default: output)"
    )
    parser.add_argument(
        "--docusaurus",
        type=str,
        default="docusaurus",
        help="Docusaurus directory (default: docusaurus)"
    )
    parser.add_argument(
        "--retriever",
        type=str,
        default="duckduckgo",
        choices=["bing", "wiki", "duckduckgo"],
        help="Retrieval method for STORM: bing, wiki, or duckduckgo (default: duckduckgo)"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress progress messages"
    )
    
    args = parser.parse_args()
    
    # Setup progress callback
    callback: Optional[Callable[[str], None]] = None if args.quiet else progress_callback
    
    try:
        # Step 1: Read and validate input
        if callback:
            callback("Reading input file...")
        
        input_handler = InputHandler(args.input)
        input_data = input_handler.read()
        
        topic = input_handler.get_topic()
        language = input_handler.get_language()
        audience = input_handler.get_audience()
        
        if callback:
            callback(f"Input validated: Topic='{topic}', Language='{language}', Audience='{audience}'")
        
        # Step 2: Initialize orchestrator
        if callback:
            callback("Initializing orchestrator...")
        
        orchestrator = Orchestrator(
            language=language,
            retriever=args.retriever,
            output_dir=args.output
        )
        
        # Step 3: Run pipeline
        if callback:
            callback("Starting pipeline execution...")
        
        result = orchestrator.run_pipeline(
            topic=topic,
            audience=audience,
            progress_callback=callback
        )
        
        if callback:
            callback("Pipeline execution completed!")
        
        # Step 4: Convert to Docusaurus
        if callback:
            callback("Converting to Docusaurus format...")
        
        converter = DocusaurusConverter(
            content_dir=result["content_dir"],
            docusaurus_dir=args.docusaurus
        )
        
        conversion_result = converter.convert(
            outline=result["outline"],
            language=language
        )
        
        # Save sidebar configuration
        sidebar_config = conversion_result["sidebar_config"]
        converter.save_sidebar_config(sidebar_config)
        
        if callback:
            callback("Docusaurus conversion completed!")
        
        # Step 5: Save summary
        summary_file = orchestrator.save_summary()
        
        if callback:
            callback(f"Summary saved to: {summary_file}")
        
        # Print final summary
        print("\n" + "="*60)
        print("PIPELINE COMPLETED SUCCESSFULLY")
        print("="*60)
        print(f"Topic: {topic}")
        print(f"Language: {language}")
        print(f"Audience: {audience}")
        print(f"\nGenerated:")
        print(f"  - Parts: {len(result['outline'].get('parts', []))}")
        total_chapters = sum(
            len(part.get("chapters", []))
            for part in result['outline'].get('parts', [])
        )
        print(f"  - Chapters: {total_chapters}")
        print(f"  - Content files: {len(conversion_result['converted_files'])}")
        print(f"\nOutput locations:")
        print(f"  - Outline: {result['outline_file']}")
        print(f"  - Content: {result['content_dir']}")
        print(f"  - Docusaurus docs: {conversion_result['docs_dir']}")
        print(f"  - Summary: {summary_file}")
        print(f"\nTo preview Docusaurus site:")
        print(f"  cd {args.docusaurus}")
        print(f"  npm install")
        print(f"  npm start")
        print("="*60)
        
        # Cleanup
        orchestrator.cleanup()
        
        return 0
        
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Validation Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

