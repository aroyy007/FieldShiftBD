# AI disclosure

This page lists every AI tool used to build FieldShift BD and its videos, what each one did, and what data it worked on. NASA Space Apps asks teams to declare AI use; this is our declaration.

## While building the project

| Tool | What we used it for | Data it saw |
| --- | --- | --- |
| Claude Code (Anthropic) and Codex (OpenAI), as coding assistants | Helping plan the system architecture, review code, write and run tests, draft documentation, and record app screens for the demo video | This repository's source code, test output and documentation |

Team Zero Requiem designed the product, chose the data sources, made the agronomy and evidence decisions, and reviewed every change before it was merged. The assistants worked inside our repository under our direction; they did not decide what the app recommends to farmers.

## Inside the app

| Feature | Model | Input | How the result is used |
| --- | --- | --- | --- |
| Leaf disease screening | ResNet50 classifier by Saon110, trained on a Bangladesh crop and vegetable disease dataset (94 conditions). [Model card](https://huggingface.co/Saon110/bd-crop-vegetable-plant-disease-model), CC BY-NC 4.0 | The farmer's leaf photo | Shown as a screening result, never a diagnosis. Results below the confidence threshold are reported as uncertain. The app tells the farmer to confirm with a local agriculture officer |
| Scan double-check (optional) | Google Gemini API | The leaf photo, crop and growth stage | A second opinion shown next to the model's result; it does not replace it |
| Farm chat (optional) | Google Gemini API | The farmer's question and their saved farm details: crop, growth stage, tasks, weather | Answers in Bangla or English. Actions the chat suggests need the farmer's explicit confirmation before anything changes |
| Bangla voice input | The phone's or browser's built-in speech recognition (`bn-BD`) | The farmer's voice, on the device | Turned into text for the chat |
| Read aloud | The device's built-in text-to-speech | Chat replies | Spoken back to the farmer |

The crop recommendations, rotation comparison, planting windows and rainfall analysis use **no AI**. They are rule-based and come from NASA POWER data, BRRI and BARC publications, and the formulas in `backend/src/compute/`, so every number can be traced and reproduced.

Gemini features switch off when `GEMINI_API_KEY` is empty or `OFFLINE_MODE=true`.

## In our videos

| Tool | Use |
| --- | --- |
| Kokoro-82M text-to-speech (Apache-2.0), run locally | English voiceover |
| OpenAI Whisper `base.en` (MIT), run locally | Timing the English subtitles to the voiceover |
| macOS Vision subject lift, run locally | Cutting team portraits out of their backgrounds for the team graphic |
| OpenAI image generation | Paper-cut illustrations in the first cut of our 240-second video |

Photos of farms in the videos are real photographs from Wikimedia Commons, credited in each video. Charts in the videos are drawn from real NASA POWER data.

## What AI did not do

- It did not choose which crops or rotations to show farmers.
- It did not generate or alter any NASA, BRRI or BARC data.
- It does not make decisions for farmers. FieldShift BD supports their judgment and never replaces it.
