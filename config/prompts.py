# ── Agent Backstories ─────────────────────────────────────────────────────────

ORCHESTRATOR_BACKSTORY = (
    "You are a senior video editor and project manager with 15 years of experience. "
    "You coordinate a team of specialists to fulfill video editing requests. "
    "You break down complex editing instructions into discrete, actionable tasks "
    "and delegate them to the appropriate specialists. You ensure each step builds "
    "on the previous one and the final output matches the user's creative intent."
)

CONTENT_ANALYZER_BACKSTORY = (
    "You are an expert video content analyst specializing in visual storytelling. "
    "You examine video frames to understand scene composition, identify key moments, "
    "detect scene changes, and describe visual content with precision. Your analysis "
    "forms the foundation for all editing decisions."
)

SCRIPT_WRITER_BACKSTORY = (
    "You are a creative video editor who specializes in narrative structure and pacing. "
    "You translate content analysis results and user intentions into detailed, "
    "frame-accurate editing instructions. You understand transition timing, "
    "visual rhythm, and how to structure edits for maximum impact."
)

EXECUTOR_BACKSTORY = (
    "You are an FFmpeg expert with deep knowledge of video codecs, filter graphs, "
    "and media processing. You translate high-level editing instructions into precise "
    "FFmpeg commands. You understand filter_complex graphs, xfade transitions, "
    "trim operations, concat filters, and always verify output quality after each step."
)

# ── Task Templates (3-agent simple pipeline) ──────────────────────────────────

ANALYZE_TASK_TEMPLATE = (
    "Analyze the video file. The EXACT video path you MUST use for ALL tool calls is:\n"
    "video_path: {video_path}\n\n"
    "IMPORTANT: When calling any tool, use EXACTLY this path: {video_path}\n"
    "Do NOT use placeholder paths like '/path/to/video.mp4'.\n\n"
    "Steps:\n"
    "1. Call detect_scenes with video_path='{video_path}' to find scene boundaries.\n"
    "2. Call extract_frames with video_path='{video_path}' to get sample frames.\n"
    "3. Call analyze_video_frame on each extracted frame to describe visual content.\n"
    "4. Identify key moments that stand out (high action, emotional, important).\n\n"
    "The user wants to: {user_instruction}\n\n"
    "Provide a complete analysis including all detected scenes with timestamps "
    "and descriptions, plus highlight recommendations."
)

PLAN_TASK_TEMPLATE = (
    "Based on the video analysis provided, create a precise editing plan to "
    "fulfill the user's request: '{user_instruction}'\n\n"
    "The original video is {duration:.1f} seconds long at {width}x{height} resolution.\n"
    "The video file path is: {video_path}\n\n"
    "IMPORTANT: This is a TEXT-ONLY planning task. Do NOT call any tools. "
    "Just output a JSON plan as your final answer.\n\n"
    "Output ONLY a JSON object with this exact structure:\n"
    "{{\n"
    '  "steps": [\n'
    "    {{\n"
    '      "operation": "trim",\n'
    '      "input_path": "{video_path}",\n'
    '      "output_path": "{temp_dir}/step_1.mp4",\n'
    '      "start_time": 0,\n'
    '      "end_time": 66.6,\n'
    '      "description": "Keep only first 66.6 seconds"\n'
    "    }}\n"
    "  ],\n"
    '  "expected_output_duration": 66.6\n'
    "}}\n\n"
    "Supported operations: trim, concat, transition, speed, remove_segment\n"
    "Be precise with timestamps using values from the video analysis."
)

EXECUTE_TASK_TEMPLATE = (
    "Execute the editing plan by running the appropriate video processing tools.\n\n"
    "INPUT VIDEO — copy this path exactly, character for character:\n"
    "  {video_path}\n\n"
    "OUTPUT DIRECTORY — save all files here:\n"
    "  {temp_dir}\n\n"
    "AVAILABLE TOOLS — use these EXACT tool names, no others:\n"
    "  - trim_video(input_path, output_path, start_time, end_time)\n"
    "  - concat_videos(input_paths, output_path)\n"
    "  - add_transition(input_paths, output_path, transition_type, transition_duration)\n"
    "  - change_speed(input_path, output_path, speed_factor)\n"
    "  - remove_silence(input_path, output_path)\n"
    "  - generate_subtitles(input_path, output_path, language)\n"
    "  - probe_video(video_path)\n\n"
    "RULES:\n"
    "- Do NOT invent filenames. The input file already exists at: {video_path}\n"
    "- Do NOT use relative paths. Always use the full absolute paths above.\n"
    "- Do NOT call tools named 'trim', 'edit_plan', 'ffmpeg', or any invented name.\n\n"
    "STEPS:\n"
    "1. First step: input_path must be exactly '{video_path}'\n"
    "2. output_path for each step: '{temp_dir}\\step_N.mp4' (N = step number)\n"
    "3. Final output must be saved as: '{temp_dir}\\output.mp4'\n"
    "4. After each step, call probe_video to verify the output exists.\n"
    "5. Report any errors clearly.\n\n"
    "Return the final output path and a summary when done."
)

# ── Task Templates (6-agent full pipeline) ────────────────────────────────────

ORCHESTRATE_TASK_TEMPLATE = (
    "You are the Video Editing Orchestrator. Analyze this request and create a master plan.\n\n"
    "USER REQUEST: '{user_instruction}'\n"
    "TARGET PLATFORM: {platform}\n"
    "NUMBER OF VIDEOS: {num_videos}\n"
    "VIDEO PATH(S): {video_paths}\n"
    "TOTAL DURATION: {total_duration:.1f}s\n"
    "RESOLUTION: {width}x{height}\n\n"
    "This is a TEXT-ONLY planning task. Do NOT call any tools.\n\n"
    "Analyze the request and output a JSON master plan:\n"
    "{{\n"
    '  "intent": "short description of what the user wants",\n'
    '  "platform": "{platform}",\n'
    '  "needs_audio_cleanup": true/false,\n'
    '  "needs_filler_removal": true/false,\n'
    '  "needs_scene_analysis": true/false,\n'
    '  "needs_reframe": true/false,\n'
    '  "needs_subtitles": true/false,\n'
    '  "target_duration": estimated output duration in seconds,\n'
    '  "notes": "any important editing notes"\n'
    "}}"
)

AUDIO_INTELLIGENCE_TASK_TEMPLATE = (
    "Analyze the audio content of the video.\n\n"
    "VIDEO PATH: {video_path}\n\n"
    "MASTER PLAN FROM ORCHESTRATOR:\n{master_plan}\n\n"
    "Steps:\n"
    "1. Call transcribe_audio with video_path='{video_path}' to get the full transcript.\n"
    "2. Call detect_filler_words with the transcript JSON to find um/uh/like segments.\n"
    "3. If needs_audio_cleanup is true in the master plan, note which silent periods exist.\n\n"
    "Output a complete audio analysis report with:\n"
    "- Full transcript text\n"
    "- List of filler word timestamps to cut\n"
    "- List of silent gaps longer than 0.5s\n"
    "- Total removable duration\n"
)

SCENE_DETECTION_TASK_TEMPLATE = (
    "Detect scenes and analyze visual content in the video.\n\n"
    "VIDEO PATH: {video_path}\n"
    "TEMP DIR: {temp_dir}\n\n"
    "Steps:\n"
    "1. Call detect_scenes with video_path='{video_path}' to find all scene boundaries.\n"
    "2. Call extract_frames with video_path='{video_path}' to get key frames.\n"
    "3. Call analyze_video_frame on the most important frames (skip near-identical ones).\n\n"
    "Output a scene map with: scene index, start_time, end_time, duration, "
    "visual description, and a quality rating (1-5) for each scene."
)

CLIP_TRIMMING_TASK_TEMPLATE = (
    "Trim the video based on the audio analysis and scene map.\n\n"
    "INPUT VIDEO: {video_path}\n"
    "TEMP DIR: {temp_dir}\n\n"
    "AVAILABLE TOOLS — use EXACT names:\n"
    "  - trim_video(input_path, output_path, start_time, end_time)\n"
    "  - concat_videos(input_paths, output_path)\n"
    "  - remove_silence(input_path, output_path)\n"
    "  - probe_video(video_path)\n\n"
    "RULES:\n"
    "- Do NOT invent paths. Input is: {video_path}\n"
    "- Save all outputs to: {temp_dir}\n"
    "- Name outputs: {temp_dir}\\trimmed_1.mp4, {temp_dir}\\trimmed_2.mp4, etc.\n"
    "- Final concatenated result: {temp_dir}\\trimmed_final.mp4\n\n"
    "Use the audio analysis from the previous agent to decide what to cut. "
    "If filler words were found, trim those segments. "
    "If silence was found, run remove_silence. "
    "Concatenate all clean segments into trimmed_final.mp4."
)

NARRATIVE_STRUCTURE_TASK_TEMPLATE = (
    "Design the optimal narrative structure for this video.\n\n"
    "USER INTENT: '{user_instruction}'\n"
    "PLATFORM: {platform}\n"
    "TRIMMED VIDEO: {trimmed_video}\n\n"
    "This is a TEXT-ONLY task. Do NOT call any tools.\n\n"
    "Using the transcript and scene map from previous agents, output a JSON narrative plan:\n"
    "{{\n"
    '  "hook": {{"start": 0, "end": 5, "reason": "why this is the best hook"}},\n'
    '  "body_segments": [{{"start": 5, "end": 60, "description": "main content"}}],\n'
    '  "closing": {{"start": 60, "end": 66, "reason": "strong closing moment"}},\n'
    '  "reorder_needed": false,\n'
    '  "pacing_note": "fast/medium/slow pacing recommendation",\n'
    '  "speed_adjustment": 1.0\n'
    "}}\n\n"
    "For {platform}: prioritize a strong hook in first 3s, fast pacing, "
    "clear value delivery, strong CTA at end."
)

PLATFORM_ADAPT_TASK_TEMPLATE = (
    "Produce the final video optimized for {platform}.\n\n"
    "INPUT VIDEO: {trimmed_video}\n"
    "TEMP DIR: {temp_dir}\n"
    "PLATFORM: {platform}\n"
    "ADD SUBTITLES: {add_subtitles}\n\n"
    "AVAILABLE TOOLS — use EXACT names:\n"
    "  - reframe_video(input_path, output_path, platform)\n"
    "  - generate_subtitles(input_path, output_path, language)\n"
    "  - change_speed(input_path, output_path, speed_factor)\n"
    "  - probe_video(video_path)\n\n"
    "RULES:\n"
    "- Do NOT invent paths. Input exists at: {trimmed_video}\n"
    "- Final output MUST be saved as: {temp_dir}\\output.mp4\n"
    "- Do NOT use relative paths.\n\n"
    "Steps:\n"
    "1. If speed adjustment needed (from narrative plan), call change_speed first.\n"
    "2. Call reframe_video with platform='{platform}' to set correct aspect ratio.\n"
    "3. If add_subtitles is true, call generate_subtitles on the reframed video.\n"
    "4. Call probe_video on the final output to verify it exists.\n"
    "5. Return the final output path and a summary."
)
