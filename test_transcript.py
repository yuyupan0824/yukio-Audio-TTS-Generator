from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
import sys

# Test instance based API
try:
    print("Instantiating YouTubeTranscriptApi...")
    api = YouTubeTranscriptApi()
    
    video_id = "jNQXAC9IVRw"
    transcript_obj = api.fetch(video_id, languages=['en'])
    
    print("\nIterating over first item:")
    for item in transcript_obj:
        print(f"Item: {item}")
        print(f"Type: {type(item)}")
        break
        
    print("\nTrying TextFormatter...")
    formatter = TextFormatter()
    # Try passing transcript_obj directly
    # Check if format_transcript expects a list of dicts or just an iterable of dicts
    try:
        text = formatter.format_transcript(transcript_obj)
        print("Success! Text preview:")
        print(text[:100])
    except Exception as e:
        print(f"Formatter failed with direct object: {e}")
        # Try converting to list if it's iterable
        print("Converting to list...")
        try:
            transcript_list = list(transcript_obj)
            text = formatter.format_transcript(transcript_list)
            print("Success with list conversion! Text preview:")
            print(text[:100])
        except Exception as e2:
             print(f"List conversion formatter failed: {e2}")

except Exception as e:
    print(f"Error: {e}")
