#!/usr/bin/env python3
"""
Verify Mission Control setup before deployment.
"""
import os
import sys
import subprocess

def check(description, condition):
    status = "✅" if condition else "❌"
    print(f"{status} {description}")
    return condition

def main():
    print("\n🔍 Mission Control Setup Verification\n")
    
    all_good = True
    
    # Python version
    all_good &= check("Python 3.10+", sys.version_info >= (3, 10))
    
    # Directory structure
    all_good &= check("Mission Control dir exists", os.path.isdir("backend"))
    all_good &= check("Frontend dir exists", os.path.isdir("frontend"))
    all_good &= check("Agents dir exists", os.path.isdir("agents"))
    
    # Key files
    all_good &= check("requirements.txt exists", os.path.isfile("backend/requirements.txt"))
    all_good &= check("app.py exists", os.path.isfile("backend/app.py"))
    all_good &= check("db_init.py exists", os.path.isfile("backend/db_init.py"))
    all_good &= check("agents/__init__.py exists", os.path.isfile("agents/__init__.py"))
    all_good &= check("agents/base.py exists", os.path.isfile("agents/base.py"))
    
    # Agent files
    all_good &= check("SportsAgent exists", os.path.isfile("agents/research/sports.py"))
    all_good &= check("ExaminationAgent exists", os.path.isfile("agents/examination.py"))
    all_good &= check("ExecutionerAgent exists", os.path.isfile("agents/executioner.py"))
    
    # Frontend files
    all_good &= check("Frontend package.json exists", os.path.isfile("frontend/package.json"))
    all_good &= check("PixelOffice component exists", os.path.isfile("frontend/src/components/PixelOffice/PixelOffice.jsx"))
    all_good &= check("AgentPipeline component exists", os.path.isfile("frontend/src/components/AgentPipeline/AgentPipeline.jsx"))
    
    # Environment
    has_env = os.path.isfile(".env")
    all_good &= check(".env file exists", has_env)
    
    if has_env:
        with open(".env") as f:
            content = f.read()
            all_good &= check("  - ANTHROPIC_API_KEY set", "ANTHROPIC_API_KEY=" in content)
            all_good &= check("  - NEWSAPI_KEY set", "NEWSAPI_KEY=" in content)
    
    # Try importing key modules
    try:
        import fastapi
        all_good &= check("FastAPI importable", True)
    except:
        all_good &= check("FastAPI importable", False)
    
    try:
        import anthropic
        all_good &= check("Anthropic SDK importable", True)
    except:
        all_good &= check("Anthropic SDK importable", False)
    
    try:
        import feedparser
        all_good &= check("feedparser importable", True)
    except:
        all_good &= check("feedparser importable", False)
    
    print()
    if all_good:
        print("✅ All checks passed! Ready to deploy.\n")
        print("Next steps:")
        print("1. Terminal 1: cd ~/Desktop/NFL\\ War\\ Room && python -m uvicorn backend.app:app --reload --port 8000")
        print("2. Terminal 2: cd ~/Desktop/mission-control && source venv/bin/activate && python -m uvicorn backend.app:app --reload --port 8001")
        print("3. Terminal 3: cd ~/Desktop/mission-control/frontend && npm run dev")
        print("4. Open http://localhost:5173 in browser")
        return 0
    else:
        print("❌ Some checks failed. See above for details.\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
