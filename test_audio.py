#!/usr/bin/env python3
"""
Audio Test Script for Orange Ball Robot
Test the beep functionality to ensure audio feedback works properly.
"""

import subprocess
import os
import time

def test_beep_methods():
    """Test different methods of producing beep sounds"""
    print("Testing audio beep methods...")
    print("=" * 40)
    
    methods = [
        ("System beep command", lambda: subprocess.run(['beep'], check=False, capture_output=True, timeout=2)),
        ("Speaker test (1000Hz sine)", lambda: subprocess.run(['speaker-test', '-t', 'sine', '-f', '1000', '-l', '1'], timeout=2, check=False, capture_output=True)),
        ("Echo bell character", lambda: subprocess.run(['bash', '-c', 'echo -e "\\a"'], timeout=1, check=False, capture_output=True)),
        ("Printf bell character", lambda: os.system('printf "\\a"')),
    ]
    
    working_methods = []
    
    for name, method in methods:
        print(f"\nTesting: {name}")
        try:
            result = method()
            if isinstance(result, subprocess.CompletedProcess):
                if result.returncode == 0:
                    print(f"✅ {name} - SUCCESS")
                    working_methods.append(name)
                else:
                    print(f"❌ {name} - FAILED (return code: {result.returncode})")
            else:
                print(f"✅ {name} - SUCCESS")
                working_methods.append(name)
        except FileNotFoundError:
            print(f"❌ {name} - FAILED (command not found)")
        except subprocess.TimeoutExpired:
            print(f"⚠️ {name} - TIMEOUT (may still work)")
        except Exception as e:
            print(f"❌ {name} - FAILED ({e})")
        
        time.sleep(1)  # Brief pause between tests
    
    print("\n" + "=" * 40)
    print("Audio Test Results:")
    if working_methods:
        print(f"✅ Working methods: {', '.join(working_methods)}")
        print("Audio feedback should work with the robot!")
    else:
        print("❌ No audio methods working")
        print("Consider:")
        print("  - Installing beep: sudo apt install beep")
        print("  - Installing ALSA utils: sudo apt install alsa-utils")
        print("  - Checking audio hardware connection")
        print("  - Disabling audio in config.py: ENABLE_AUDIO = False")

def check_audio_system():
    """Check basic audio system availability"""
    print("\nChecking audio system...")
    print("-" * 30)
    
    # Check for audio devices
    try:
        result = subprocess.run(['ls', '/dev/snd/'], capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            print("✅ Audio devices found:")
            for device in result.stdout.strip().split('\n'):
                print(f"    {device}")
        else:
            print("❌ No audio devices found in /dev/snd/")
    except Exception as e:
        print(f"❌ Error checking audio devices: {e}")
    
    # Check for required packages
    packages = ['beep', 'alsa-utils']
    for package in packages:
        try:
            result = subprocess.run(['which', package], capture_output=True)
            if result.returncode == 0:
                print(f"✅ {package} is installed")
            else:
                print(f"❌ {package} is not installed")
                print(f"    Install with: sudo apt install {package}")
        except Exception as e:
            print(f"❌ Error checking {package}: {e}")

def interactive_test():
    """Interactive beep test"""
    print("\nInteractive Beep Test")
    print("-" * 30)
    print("This will play 3 beeps with 2-second intervals.")
    print("Listen for the beep sounds...")
    
    input("Press Enter to start the test...")
    
    for i in range(3):
        print(f"Beep {i+1}/3...")
        try:
            # Try the most common method first
            subprocess.run(['beep'], check=False, capture_output=True, timeout=1)
        except FileNotFoundError:
            try:
                os.system('printf "\\a"')
            except:
                print("🔊 BEEP! (text fallback)")
        
        if i < 2:  # Don't sleep after the last beep
            time.sleep(2)
    
    print("\nDid you hear the beeps? (y/n): ", end="")
    response = input().lower().strip()
    
    if response in ['y', 'yes']:
        print("✅ Great! Audio feedback is working.")
    else:
        print("❌ Audio may not be working properly.")
        print("Check the troubleshooting section in ROBOT_README.md")

def main():
    print("Orange Ball Robot - Audio Test")
    print("==============================")
    
    check_audio_system()
    test_beep_methods()
    interactive_test()
    
    print("\nAudio test completed!")
    print("If audio is working, the robot will beep when no orange ball is found.")
    print("If not working, you can disable audio in config.py: ENABLE_AUDIO = False")

if __name__ == "__main__":
    main()