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
    # Optional: Clear existing data if you want a fresh start
    # Course.objects.all().delete()
    # User.objects.exclude(is_superuser=True).delete()
    
    print("Creating Realistic LMS Sample Data...")

    # 1. Create Users
    # ---------------------------------------------------------
    # Create Admin
    admin_user, created = User.objects.get_or_create(
        username='admin',
        defaults={
            'first_name': 'System',
            'last_name': 'Administrator',
            'email': 'admin@lms.com',
            'role': 'admin',
            'is_staff': True,
            'is_superuser': True
        }
    )
    if created:
        admin_user.set_password('admin123')
        admin_user.save()

    # Create Instructors
    instructors = []
    instr_data = [
        ('instructor', 'Main', 'Instructor', 'instructor@lms.com', 'Professional Educator with 10+ years in curriculum design.'),
        ('dr_smith', 'John', 'Smith', 'smith@university.edu', 'PhD in Computer Science, specialized in AI and Python.'),
        ('prof_jones', 'Sarah', 'Jones', 'sjones@tech.io', 'Lead Data Scientist at a Fortune 500 company.'),
        ('dev_mike', 'Michael', 'Chen', 'mike@dev.com', 'Senior Full-stack Engineer and Open Source Contributor.'),
        ('design_anna', 'Anna', 'Bella', 'anna@design.com', 'Award-winning UI/UX Designer.')
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
            # Match requested passwords for demo accounts
            if username == 'instructor':
                user.set_password('instructor123')
            else:
                user.set_password('pass1234')
            user.save()
        
        # Ensure profile exists
        InstructorProfile.objects.get_or_create(
            user=user, 
            defaults={'instructor_id': f"INS-{random.randint(1000, 9999)}"}
        )
        instructors.append(user)

    # Create Students
    students = []
    std_data = [
        ('student', 'Main', 'Student', 'student@lms.com'),
        ('alice_w', 'Alice', 'Walker', 'alice@gmail.com'),
        ('bob_m', 'Bob', 'Miller', 'bob@yahoo.com'),
        ('charlie_d', 'Charlie', 'Davis', 'charlie@outlook.com'),
        ('david_h', 'David', 'Harris', 'david@example.com'),
        ('eva_g', 'Eva', 'Green', 'eva@gmail.com'),
        ('frank_t', 'Frank', 'Thomas', 'frank@tech.com'),
        ('grace_k', 'Grace', 'Kim', 'grace@kim.io'),
        ('henry_v', 'Henry', 'Vance', 'henry@vance.io'),
        ('isabel_s', 'Isabel', 'Stone', 'isabel@stone.com')
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
            if username == 'student':
                user.set_password('student123')
            else:
                user.set_password('pass1234')
            user.save()
        
        # Ensure profile exists
        StudentProfile.objects.get_or_create(
            user=user, 
            defaults={'student_id': f"STU-{random.randint(10000, 99999)}"}
        )
        students.append(user)

    # 2. Create Courses
    # ---------------------------------------------------------
    course_configs = [
        {
            'title': 'Python Magic: Zero to Hero',
            'desc': 'Master Python by building 20+ professional projects. Includes Automation, Web Scraping, and Data Science.',
            'instr': instructors[1],
            'cat': 'Programming',
            'dur': '12 Weeks',
            'diff': 'beginner'
        },
        {
            'title': 'Advanced React & Next.js 14',
            'desc': 'Build high-performance web applications with Server Components, App Router, and TypeScript.',
            'instr': instructors[3],
            'cat': 'Web Development',
            'dur': '8 Weeks',
            'diff': 'advanced'
        },
        {
            'title': 'Data Science Bootcamp 2024',
            'desc': 'The most comprehensive path to becoming a Data Scientist. Covers SQL, Tableau, and Machine Learning.',
            'instr': instructors[2],
            'cat': 'Data Science',
            'dur': '16 Weeks',
            'diff': 'intermediate'
        },
        {
            'title': 'UI/UX Design Masterclass',
            'desc': 'Learn Figma, user research, and prototyping. Design stunning interfaces that users love.',
            'instr': instructors[4],
            'cat': 'Design',
            'dur': '6 Weeks',
            'diff': 'beginner'
        },
        {
            'title': 'Django Enterprise Patterns',
            'desc': 'Scaling Django applications, building robust APIs with DRF, and deploying with Docker.',
            'instr': instructors[0],
            'cat': 'Backend',
            'dur': '10 Weeks',
            'diff': 'advanced'
        }
    ]

    courses = []
    for ccfg in course_configs:
        course, created = Course.objects.get_or_create(
            title=ccfg['title'],
            defaults={
                'description': ccfg['desc'],
                'instructor': ccfg['instr'],
                'category': ccfg['cat'],
                'duration': ccfg['dur'],
                'difficulty': ccfg['diff'],
                'status': 'published'
            }
        )
        courses.append(course)

    # 3. Create Lessons
    # ---------------------------------------------------------
    for course in courses:
        modules = [
            "Getting Started & Setup",
            "Core Concepts & Syntax",
            "Intermediate Patterns",
            "Real-world Implementation",
            "Final Project Walkthrough"
        ]
        for idx, mod_name in enumerate(modules):
            Lesson.objects.get_or_create(
                course=course,
                title=f"Module {idx+1}: {mod_name}",
                defaults={
                    'content': f"<p>This lesson covers <b>{mod_name}</b> for the {course.title} course. Learn industry secrets and best practices.</p>",
                    'order': idx + 1,
                    'duration': random.randint(30, 90)
                }
            )

    # 4. Create Enrollments
    # ---------------------------------------------------------
    for student in students:
        # Each student enrolls in 2-4 random courses
        target_courses = random.sample(courses, random.randint(2, 4))
        for course in target_courses:
            Enrollment.objects.get_or_create(
                student=student,
                course=course,
                defaults={
                    'progress': random.randint(0, 100),
                    'status': 'active'
                }
            )

    # 5. Create Assignments & Submissions
    # ---------------------------------------------------------
    for course in courses:
        assignment, _ = Assignment.objects.get_or_create(
            course=course,
            title=f"Final Assessment: {course.category} Mastery",
            defaults={
                'description': f"Submit your comprehensive project covering all lessons in {course.title}.",
                'max_score': 100,
                'due_date': timezone.now() + timedelta(days=random.randint(5, 30)),
                'assignment_type': 'project'
            }
        )
        
        # Add some submissions for enrolled students
        enrollees = Enrollment.objects.filter(course=course)
        for enrollment in enrollees:
            if random.random() > 0.3: # 70% chance they submitted something
                submission, _ = Submission.objects.get_or_create(
                    assignment=assignment,
                    student=enrollment.student,
                    defaults={
                        'content': f"Check out my GitHub repository for the final project of {course.title}. I implemented all requested features.",
                        'status': 'graded' if random.random() > 0.4 else 'submitted'
                    }
                )
                
                if submission.status == 'graded':
                    Grade.objects.get_or_create(
                        submission=submission,
                        defaults={
                            'score': random.randint(70, 100),
                            'feedback': "Great implementation! Excellent attention to detail.",
                            'graded_by': course.instructor
                        }
                    )

    print("\n[SUCCESS] Realistic dummy data has been injected!")
    print(f"Total Users: {User.objects.count()}")
    print(f"Total Courses: {Course.objects.count()}")
    print(f"Total Enrollments: {Enrollment.objects.count()}")
    print(f"Total Submissions: {Submission.objects.count()}")

if __name__ == '__main__':
    create_sample_data()
