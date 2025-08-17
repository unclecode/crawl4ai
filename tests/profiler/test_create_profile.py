from crawl4ai import BrowserProfiler
import asyncio


if __name__ == "__main__":
    # Example usage
    profiler = BrowserProfiler()
    
    # Create a new profile
    import os
    from pathlib import Path
    home_dir = Path.home()
    profile_path = asyncio.run(profiler.create_profile( str(home_dir / ".crawl4ai/profiles/test-profile")))
    
    print(f"Profile created at: {profile_path}")

        
            
    # # Launch a standalone browser
    # asyncio.run(profiler.launch_standalone_browser())
    
    # # List profiles
    # profiles = profiler.list_profiles()
    # for profile in profiles:
    #     print(f"Profile: {profile['name']}, Path: {profile['path']}")
    
    # # Delete a profile
    # success = profiler.delete_profile("my-profile")
    # if success:
    #     print("Profile deleted successfully")
    # else:
    #     print("Failed to delete profile")