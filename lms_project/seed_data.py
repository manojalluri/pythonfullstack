import os
import django
import random
from datetime import timedelta
from django.utils import timezone

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lms_project.settings')
django.setup()

from accounts.models import User, StudentProfile, InstructorProfile
from courses.models import Course, Lesson, Enrollment, Material
from assignments.models import Assignment, Submission, Grade

def create_sample_data():
    print("Deleting old data...")
    # Clear existing data to avoid duplicates, but keep admins if needed
    # (Optional: User.objects.exclude(role='admin').delete())
    
    print("Creating Realistic LMS Sample Data...")

    # 1. Create Users
    roles = ['student', 'instructor']
    
    # Create Instructors
    instructors = []
    instr_data = [
        ('dr_smith', 'John', 'Smith', 'smith@example.com', 'Senior Developer with 15 years of experience in Python and AI.'),
        ('prof_jones', 'Sarah', 'Jones', 'jones@example.com', 'Data Scientist specialized in Machine Learning and Big Data.'),
        ('dev_mike', 'Michael', 'Chen', 'chen@example.com', 'Full-stack Architect focused on React, Node.js and Cloud Computing.')
    ]
    
    for username, first, last, email, bio in instr_data:
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'first_name': first,
                'last_name': last,
                'email': email,
                'role': 'instructor',
                'bio': bio
            }
        )
        if created:
            user.set_password('pass1234')
            user.save()
        instructors.append(user)

    # Create Students
    students = []
    std_data = [
        ('alice_w', 'Alice', 'Walker', 'alice@example.com'),
        ('bob_m', 'Bob', 'Miller', 'bob@example.com'),
        ('charlie_d', 'Charlie', 'Davis', 'charlie@example.com'),
        ('david_h', 'David', 'Harris', 'david@example.com'),
        ('eva_g', 'Eva', 'Green', 'eva@example.com')
    ]
    
    for username, first, last, email in std_data:
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'first_name': first,
                'last_name': last,
                'email': email,
                'role': 'student'
            }
        )
        if created:
            user.set_password('pass1234')
            user.save()
        students.append(user)

    # 2. Create Courses
    course_list = [
        {
            'title': 'Mastering Python for Data Science',
            'desc': 'From basics to advanced data analysis with Pandas, NumPy, and Matplotlib.',
            'instr': instructors[0],
            'cat': 'Programming',
            'dur': '10 Weeks',
            'diff': 'intermediate'
        },
        {
            'title': 'The Ultimate Web Development Bootcamp',
            'desc': 'Learn HTML, CSS, JavaScript, React, and Django by building real projects.',
            'instr': instructors[2],
            'cat': 'Web Development',
            'dur': '12 Weeks',
            'diff': 'beginner'
        },
        {
            'title': 'Machine Learning Fundamentals',
            'desc': 'Deep dive into linear regression, classification, and neural networks.',
            'instr': instructors[1],
            'cat': 'Artificial Intelligence',
            'dur': '8 Weeks',
            'diff': 'advanced'
        }
    ]

    courses = []
    for cdata in course_list:
        course, created = Course.objects.get_or_create(
            title=cdata['title'],
            defaults={
                'description': cdata['desc'],
                'instructor': cdata['instr'],
                'category': cdata['cat'],
                'duration': cdata['dur'],
                'difficulty': cdata['diff'],
                'status': 'published'
            }
        )
        courses.append(course)

    # 3. Create Lessons for each course
    for course in courses:
        for i in range(1, 4):
            Lesson.objects.get_or_create(
                course=course,
                title=f'Module {i}: Introduction to {course.title.split()[0]}',
                defaults={
                    'content': f'<p>Welcome to Module {i}. This lesson covers the core concepts of {course.category}.</p>',
                    'order': i,
                    'duration': 45
                }
            )

    # 4. Create Enrollments
    for student in students:
        # Each student enrolls in 1-2 random courses
        enrolled_courses = random.sample(courses, random.randint(1, 2))
        for course in enrolled_courses:
            Enrollment.objects.get_or_create(
                student=student,
                course=course,
                defaults={
                    'progress': random.randint(10, 85)
                }
            )

    # 5. Create Assignments & Submissions
    for course in courses:
        assignment, created = Assignment.objects.get_or_create(
            course=course,
            title=f'First Project: {course.title}',
            defaults={
                'description': 'Implement the concepts learned in the first three modules.',
                'max_score': 100,
                'due_date': timezone.now() + timedelta(days=7),
                'assignment_type': 'project'
            }
        )
        
        # Create some submissions
        enrolled_students = Enrollment.objects.filter(course=course).values_list('student', flat=True)
        for student_id in list(enrolled_students)[:3]: # Grade for first 3 students
            student = User.objects.get(id=student_id)
            submission, created = Submission.objects.get_or_create(
                assignment=assignment,
                student=student,
                defaults={
                    'content': 'This is my project submission content. I followed all instructions.',
                    'status': 'graded' if random.choice([True, False]) else 'submitted'
                }
            )
            
            if submission.status == 'graded':
                Grade.objects.get_or_create(
                    submission=submission,
                    defaults={
                        'score': random.randint(75, 98),
                        'feedback': 'Excellent work! You demonstrated a deep understanding of the subject.',
                        'graded_by': course.instructor
                    }
                )

    print("Successfully created realistic sample data!")
    print(f"Users: {User.objects.count()}")
    print(f"Courses: {Course.objects.count()}")
    print(f"Enrollments: {Enrollment.objects.count()}")

if __name__ == '__main__':
    create_sample_data()
