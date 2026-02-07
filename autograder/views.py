# views.py - COMPLETE WORKING VERSION

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth import authenticate, login
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.files.storage import default_storage
from .models import Question, StudentAnswer
from .ocr_engine import run_ocr
from .text_correction import safe_correct_word, load_fixes
from .grader import grade_text
import re
import os
import traceback

# ========== HOME PAGE ==========
def home(request):
    return render(request, 'home.html')

# ========== TEACHER VIEWS ==========
def teacher_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_staff:
            login(request, user)
            return redirect('teacher_dashboard')
        else:
            return render(request, 'teacher_login.html', {'error': 'Invalid credentials'})
    return render(request, 'teacher_login.html')

@login_required
def teacher_dashboard(request):
    questions = Question.objects.filter(created_by=request.user)
    return render(request, 'teacher_dashboard.html', {'questions': questions})

@login_required
def add_question(request):
    extracted_data = None
    
    if request.method == 'POST' and 'question_image' in request.FILES:
        image = request.FILES['question_image']
        filename = f"temp_{image.name}"
        saved_path = default_storage.save(filename, image)
        full_path = default_storage.path(saved_path)
        
        try:
            # Run OCR on image
            raw_results = run_ocr(full_path)
            full_text = " ".join(raw_results).strip()
            
            # Auto-split questions
            questions = split_into_questions(full_text)
            
            # Save each question
            for q_num, q_text in questions.items():
                # Clean question number
                q_num = re.sub(r'[^Q\d]', '', q_num)
                
                # Save question
                question = Question(
                    question_number=q_num,
                    question_text=q_text,
                    model_answer=request.POST.get(f'model_answer_{q_num}', ''),
                    keywords=request.POST.get(f'keywords_{q_num}', ''),
                    created_by=request.user,
                    question_image=image  # Save original image for all
                )
                question.save()
            
            return redirect('view_questions')
            
        except Exception as e:
            messages.error(request, f"Error processing image: {str(e)}")
        finally:
            if os.path.exists(full_path):
                os.remove(full_path)
    
    return render(request, 'add_question.html', {
        'questions': [],  # No dropdown needed
        'extracted_data': None
    })

@login_required
def view_questions(request):
    questions = Question.objects.filter(created_by=request.user).order_by('question_number')
    return render(request, 'view_questions.html', {'questions': questions})

# ========== STUDENT VIEWS ==========
def student_upload(request):
    if request.method == 'POST':
        # ✅ FIXED: Get student details from POST
        student_name = request.POST.get('student_name', '').strip()
        roll_number = request.POST.get('roll_number', '').strip()
        
        if not student_name or not roll_number:
            return render(request, 'student_upload.html', {
                'error': 'Student name and roll number are required!'
            })
        
        if 'answer_image' not in request.FILES:
            return render(request, 'student_upload.html', {
                'error': 'Please upload an answer sheet image!'
            })
        
        # Save image temporarily
        image = request.FILES['answer_image']
        filename = f"temp_{image.name}"
        saved_path = default_storage.save(filename, image)
        full_path = default_storage.path(saved_path)
        
        try:
            # Process OCR
            raw_results = run_ocr(full_path)
            full_text = " ".join(raw_results).strip()
            
            # Auto-detect question number
            question_number = identify_question_number(full_text)
            
            # If not detected, try splitting
            if not question_number:
                questions = split_into_questions(full_text)
                if questions:
                    # Use first question
                    question_number = next(iter(questions.keys()))
                else:
                    return render(request, 'student_upload.html', {
                        'error': 'Could not detect question number. Please write Q1/Q2/Q3 clearly.'
                    })
            
            # Get question from database
            try:
                question = Question.objects.get(question_number=question_number)
            except Question.DoesNotExist:
                return render(request, 'student_upload.html', {
                    'error': f'Question {question_number} not found in database!'
                })
            
            # Grade against database keywords
            score, matched, missing = grade_against_question(full_text, question)
            
            # Save to database
            answer = StudentAnswer.objects.create(
                student_name=student_name,
                roll_number=roll_number,
                question=question,
                answer_image=image,
                extracted_text=full_text,
                score=score,
                matched_keywords=','.join(matched),
                missing_keywords=','.join(missing)
            )
            
            return redirect('view_result', answer_id=answer.id)
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            traceback.print_exc()
            return render(request, 'student_upload.html', {
                'error': f'Processing failed: {str(e)}'
            })
        finally:
            if os.path.exists(full_path):
                os.remove(full_path)
            if default_storage.exists(filename):
                default_storage.delete(filename)
    
    return render(request, 'student_upload.html', {})

def view_result(request, answer_id):
    answer = get_object_or_404(StudentAnswer, id=answer_id)
    return render(request, 'result.html', {'answer': answer})

# ========== SIMPLE TEST (For Debugging) ==========
@csrf_exempt
def simple_grade(request):
    if request.method == 'POST' and request.FILES.get('image'):
        image = request.FILES['image']
        filename = f"temp_{image.name}"
        saved_path = default_storage.save(filename, image)
        full_path = default_storage.path(saved_path)

        try:
            raw_results = run_ocr(full_path)
            ocr_fixes = load_fixes()
            
            all_tokens = []
            corrected_lines = []
            for line in raw_results:
                tokens = line.split()
                corrected_tokens = []
                for token in tokens:
                    if not token or not any(c.isalpha() for c in token):
                        continue
                    all_tokens.append(token)
                    corrected = safe_correct_word(token, ocr_fixes)
                    if corrected:
                        corrected_tokens.append(corrected)
                if corrected_tokens:
                    corrected_lines.append(" ".join(corrected_tokens))

            final_text = " ".join(corrected_lines).strip()
            
            # Use OLD grading function
            score, matched, missing = grade_text(final_text)

            return JsonResponse({
                "success": True,
                "grade": round(score, 2),
                "corrected_text": final_text,
                "matched": list(matched),
                "missing": list(missing)
            })

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
        finally:
            if os.path.exists(full_path):
                os.remove(full_path)

def simple_test_page(request):
    return render(request, 'simple_test.html')

# ========== HELPER FUNCTIONS ==========
def identify_question_number(extracted_text):
    """Auto-identify question number from extracted text - More robust"""
    text_lower = extracted_text.lower()
    
    # Try exact matches first
    if re.search(r'\bq\s*1\b|\bquestion\s*1\b|\bquestion\s*no\s*1\b', text_lower):
        return 'Q1'
    elif re.search(r'\bq\s*2\b|\bquestion\s*2\b|\bquestion\s*no\s*2\b', text_lower):
        return 'Q2'
    elif re.search(r'\bq\s*3\b|\bquestion\s*3\b|\bquestion\s*no\s*3\b', text_lower):
        return 'Q3'
    elif re.search(r'\bq\s*4\b|\bquestion\s*4\b|\bquestion\s*no\s*4\b', text_lower):
        return 'Q4'
    elif re.search(r'\bq\s*5\b|\bquestion\s*5\b|\bquestion\s*no\s*5\b', text_lower):
        return 'Q5'
    
    # Try fuzzy matching if exact fails
    if 'q1' in text_lower or 'question1' in text_lower:
        return 'Q1'
    elif 'q2' in text_lower or 'question2' in text_lower:
        return 'Q2'
    elif 'q3' in text_lower or 'question3' in text_lower:
        return 'Q3'
    
    # Last resort: check first few characters
    first_20 = text_lower[:20]
    if 'q1' in first_20 or '1' in first_20:
        return 'Q1'
    elif 'q2' in first_20 or '2' in first_20:
        return 'Q2'
    elif 'q3' in first_20 or '3' in first_20:
        return 'Q3'
    
    return None

def grade_against_question(student_text, question):
    student_words = set(student_text.lower().split())
    expected_keywords = set(question.get_keywords_list())
    
    matched = student_words & expected_keywords
    missing = expected_keywords - matched
    score = len(matched) / len(expected_keywords) if expected_keywords else 0
    
    return score, matched, missing

def split_into_questions(full_text):
    """
    Auto-split text into Q1, Q2, Q3 based on patterns like "Q1_", "Q2.", "Q3."
    """
    # Find all question markers
    # Pattern: Q followed by number, then any punctuation or space
    pattern = r'(Q\d+[._: ]+)'
    
    # Find all matches
    matches = re.finditer(pattern, full_text)
    
    # Get positions of all matches
    positions = [m.start() for m in matches]
    
    # If no matches found, fallback to Q1
    if not positions:
        return {'Q1': full_text}
    
    # Add end position
    positions.append(len(full_text))
    
    # Extract questions
    questions = {}
    for i in range(len(positions)-1):
        start = positions[i]
        end = positions[i+1]
        
        # Extract question text
        q_text = full_text[start:end].strip()
        
        # Extract question number
        q_num_match = re.search(r'Q\d+', q_text)
        if not q_num_match:
            continue
        q_num = q_num_match.group(0)
        
        # Remove question number from text
        q_text = re.sub(r'^Q\d+[._: ]+', '', q_text, count=1).strip()
        
        # If there's another question marker in the text, split it
        next_question = re.search(r'Q\d+', q_text)
        if next_question:
            q_text = q_text[:next_question.start()].strip()
        
        # Remove any trailing question marks or punctuation
        q_text = re.sub(r'[.?!]+$', '', q_text).strip()
        
        # Add to questions dictionary
        questions[q_num] = q_text
    
    return questions