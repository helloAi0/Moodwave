import asyncio
from concurrent.futures import ThreadPoolExecutor
from app.services.emotion_engine import EmotionEngineV2
from app.services.socket_manager import broadcast_mood

executor = ThreadPoolExecutor(max_workers=3)
engine = EmotionEngineV2()

async def process_ai_frame(frame):
    """
    Runs the heavy DeepFace logic in a separate thread 
    so the web server stays responsive.
    """
    loop = asyncio.get_event_loop()
    
    # 1. Detect (This is the heavy part)
    # result = await loop.run_in_executor(executor, deepface_logic, frame)
    
    # 2. Update Engine V2
    # mock_emotion for testing Phase 1
    analysis = engine.process_frame("neutral") 
    
    # 3. Push to Frontend via WebSocket
    await broadcast_mood(analysis)