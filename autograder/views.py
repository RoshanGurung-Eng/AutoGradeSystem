# autograder/views.py
import os
import json
import re
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from .ocr_engine import run_ocr
from .text_correction import safe_correct_word, auto_build_ocr_fixes
from .grader import grade_text
from .config import MODEL_ANSWER
# from django.shortcuts import render, redirect


# Helper: load fixes from JSON
def load_fixes():
    path = os.path.join(os.path.dirname(__file__), 'ocr_fixes.json')
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return {}

# Helper: save fixes
def save_fixes(fixes):
    path = os.path.join(os.path.dirname(__file__), 'ocr_fixes.json')
    with open(path, 'w') as f:
        json.dump(fixes, f, indent=2)

@csrf_exempt
def grade_answer(request):
    if request.method == 'POST' and request.FILES.get('image'):
        image = request.FILES['image']
        filename = f"temp_{image.name}"
        saved_path = default_storage.save(filename, image)
        full_path = default_storage.path(saved_path)

        try:
            # 1. Run OCR
            raw_results = run_ocr(full_path)
            print("Raw OCR:", raw_results)  # for debugging

            # 2. Load fixes
            ocr_fixes = load_fixes()

            # 3. Tokenize & correct
            all_tokens = []
            corrected_lines = []
            for line in raw_results:
                tokens = re.split(r'[_\s~@#$%^&*+=]+', line)
                corrected_tokens = []
                for token in tokens:
                    if not token or not any(c.isalpha() for c in token):
                        continue
                    all_tokens.append(token)
                    corrected = safe_correct_word(token, ocr_fixes)
                    if corrected:
                        corrected_tokens.append(corrected)
                corrected_lines.append(" ".join(corrected_tokens))

            final_text = " ".join(corrected_lines).strip()
            print("Corrected:", final_text)

            # 4. Auto-generate new fixes
            model_words = set(MODEL_ANSWER.lower().split())
            new_fixes = auto_build_ocr_fixes(all_tokens, model_words)
            ocr_fixes.update(new_fixes)
            save_fixes(ocr_fixes)

            # 5. Grade
            score, matched, missing = grade_text(final_text)

            return JsonResponse({
                "success": True,
                "grade": round(score, 2),
                "corrected_text": final_text,
                "matched": list(matched),
                "missing": list(missing),
                "new_fixes_added": len(new_fixes)
            })

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
        finally:
            if os.path.exists(full_path):
                os.remove(full_path)

    return JsonResponse({"error": "POST with image required"}, status=400)

