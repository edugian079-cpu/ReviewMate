import streamlit as st
import sqlite3
from datetime import datetime

# =========================================================
# DATABASE
# =========================================================

DB_NAME = "reviewmate.db"


def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)


def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    # Questions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL,
            quiz_name TEXT NOT NULL,
            question TEXT NOT NULL,
            option_a TEXT NOT NULL,
            option_b TEXT NOT NULL,
            option_c TEXT NOT NULL,
            option_d TEXT NOT NULL,
            correct_answer TEXT NOT NULL
        )
    """)

    # Quiz attempts table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL,
            quiz_name TEXT NOT NULL,
            score INTEGER NOT NULL,
            total INTEGER NOT NULL,
            percentage REAL NOT NULL,
            date_taken TEXT NOT NULL
        )
    """)

    # Individual answers table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attempt_answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            attempt_id INTEGER NOT NULL,
            question TEXT NOT NULL,
            selected_answer TEXT,
            correct_answer TEXT NOT NULL,
            is_correct INTEGER NOT NULL,
            FOREIGN KEY (attempt_id) REFERENCES attempts(id)
        )
    """)

    conn.commit()
    conn.close()


create_tables()


# =========================================================
# DATABASE FUNCTIONS
# =========================================================

def add_question(
    subject,
    quiz_name,
    question,
    option_a,
    option_b,
    option_c,
    option_d,
    correct_answer
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO questions (
            subject,
            quiz_name,
            question,
            option_a,
            option_b,
            option_c,
            option_d,
            correct_answer
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        subject,
        quiz_name,
        question,
        option_a,
        option_b,
        option_c,
        option_d,
        correct_answer
    ))

    conn.commit()
    conn.close()


def get_subjects():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DISTINCT subject
        FROM questions
        ORDER BY subject
    """)

    subjects = [row[0] for row in cursor.fetchall()]

    conn.close()

    return subjects


def get_quizzes(subject=None):
    conn = get_connection()
    cursor = conn.cursor()

    if subject:
        cursor.execute("""
            SELECT DISTINCT quiz_name
            FROM questions
            WHERE subject = ?
            ORDER BY quiz_name
        """, (subject,))
    else:
        cursor.execute("""
            SELECT DISTINCT quiz_name
            FROM questions
            ORDER BY quiz_name
        """)

    quizzes = [row[0] for row in cursor.fetchall()]

    conn.close()

    return quizzes


def get_questions(subject, quiz_name):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            question,
            option_a,
            option_b,
            option_c,
            option_d,
            correct_answer
        FROM questions
        WHERE subject = ?
        AND quiz_name = ?
        ORDER BY id
    """, (subject, quiz_name))

    questions = cursor.fetchall()

    conn.close()

    return questions


def get_all_questions():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            subject,
            quiz_name,
            question,
            option_a,
            option_b,
            option_c,
            option_d,
            correct_answer
        FROM questions
        ORDER BY subject, quiz_name, id
    """)

    questions = cursor.fetchall()

    conn.close()

    return questions


def delete_question(question_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM questions
        WHERE id = ?
    """, (question_id,))

    conn.commit()
    conn.close()


def save_attempt(
    subject,
    quiz_name,
    score,
    total,
    percentage,
    answers
):
    conn = get_connection()
    cursor = conn.cursor()

    date_taken = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        INSERT INTO attempts (
            subject,
            quiz_name,
            score,
            total,
            percentage,
            date_taken
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        subject,
        quiz_name,
        score,
        total,
        percentage,
        date_taken
    ))

    attempt_id = cursor.lastrowid

    for answer in answers:
        cursor.execute("""
            INSERT INTO attempt_answers (
                attempt_id,
                question,
                selected_answer,
                correct_answer,
                is_correct
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            attempt_id,
            answer["question"],
            answer["selected"],
            answer["correct"],
            answer["correct"] == answer["selected"]
        ))

    conn.commit()
    conn.close()

    return attempt_id


def get_attempts():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            subject,
            quiz_name,
            score,
            total,
            percentage,
            date_taken
        FROM attempts
        ORDER BY id DESC
    """)

    attempts = cursor.fetchall()

    conn.close()

    return attempts


def get_attempt_answers(attempt_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            question,
            selected_answer,
            correct_answer,
            is_correct
        FROM attempt_answers
        WHERE attempt_id = ?
    """, (attempt_id,))

    answers = cursor.fetchall()

    conn.close()

    return answers


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="ReviewMate",
    page_icon="📚",
    layout="wide"
)


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown("""
<style>

.main-title {
    font-size: 42px;
    font-weight: bold;
    margin-bottom: 0px;
}

.subtitle {
    font-size: 18px;
    margin-bottom: 25px;
}

.card {
    padding: 20px;
    border-radius: 12px;
    border: 1px solid #ddd;
    margin-bottom: 15px;
}

.correct {
    padding: 10px;
    border-radius: 8px;
}

.incorrect {
    padding: 10px;
    border-radius: 8px;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# SESSION STATE
# =========================================================

if "quiz_started" not in st.session_state:
    st.session_state.quiz_started = False

if "quiz_submitted" not in st.session_state:
    st.session_state.quiz_submitted = False

if "quiz_questions" not in st.session_state:
    st.session_state.quiz_questions = []

if "quiz_subject" not in st.session_state:
    st.session_state.quiz_subject = ""

if "quiz_name" not in st.session_state:
    st.session_state.quiz_name = ""

if "last_attempt_id" not in st.session_state:
    st.session_state.last_attempt_id = None


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title("📚 ReviewMate")

st.sidebar.write("Student Reviewer and Quiz Management System")

page = st.sidebar.radio(
    "Navigation",
    [
        "🏠 Dashboard",
        "📝 Take Quiz",
        "➕ Create Question",
        "📋 Question Sets",
        "📊 Quiz History"
    ]
)


# =========================================================
# DASHBOARD
# =========================================================

if page == "🏠 Dashboard":

    st.markdown(
        '<div class="main-title">📚 ReviewMate</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">Your Student Reviewer and Quiz Management System</div>',
        unsafe_allow_html=True
    )

    questions = get_all_questions()
    attempts = get_attempts()
    subjects = get_subjects()
    quizzes = get_quizzes()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "📚 Subjects",
            len(subjects)
        )

    with col2:
        st.metric(
            "📝 Quizzes",
            len(quizzes)
        )

    with col3:
        st.metric(
            "❓ Questions",
            len(questions)
        )

    with col4:
        st.metric(
            "📊 Attempts",
            len(attempts)
        )

    st.divider()

    st.subheader("Welcome to ReviewMate!")

    st.write(
        """
        ReviewMate helps students review their lessons by using
        organized question sets and practice quizzes.

        You can create questions, take quizzes, automatically calculate
        your score, and review your previous attempts.
        """
    )

    if attempts:

        st.subheader("📈 Recent Quiz Attempts")

        recent_attempts = attempts[:5]

        for attempt in recent_attempts:

            attempt_id, subject, quiz_name, score, total, percentage, date_taken = attempt

            st.write(
                f"**{quiz_name}** - {subject} | "
                f"Score: **{score}/{total}** "
                f"({percentage:.1f}%) | {date_taken}"
            )

    else:

        st.info(
            "No quiz attempts yet. Take your first quiz to see your results here."
        )


# =========================================================
# TAKE QUIZ
# =========================================================

elif page == "📝 Take Quiz":

    st.title("📝 Take a Quiz")

    subjects = get_subjects()

    if not subjects:

        st.warning(
            "There are no questions yet. Create a question first."
        )

    else:

        selected_subject = st.selectbox(
            "Select Subject",
            subjects
        )

        quizzes = get_quizzes(selected_subject)

        if quizzes:

            selected_quiz = st.selectbox(
                "Select Quiz",
                quizzes
            )

            questions = get_questions(
                selected_subject,
                selected_quiz
            )

            st.write(
                f"**Number of Questions:** {len(questions)}"
            )

            if not st.session_state.quiz_started:

                if st.button(
                    "▶️ Start Quiz",
                    use_container_width=True
                ):

                    st.session_state.quiz_started = True
                    st.session_state.quiz_submitted = False
                    st.session_state.quiz_questions = questions
                    st.session_state.quiz_subject = selected_subject
                    st.session_state.quiz_name = selected_quiz

                    st.rerun()

            else:

                # Check if the selected quiz changed
                if (
                    st.session_state.quiz_subject != selected_subject
                    or st.session_state.quiz_name != selected_quiz
                ):

                    st.session_state.quiz_started = False
                    st.session_state.quiz_submitted = False
                    st.rerun()

                st.subheader(
                    f"{st.session_state.quiz_name}"
                )

                st.write(
                    f"Subject: **{st.session_state.quiz_subject}**"
                )

                st.divider()

                # -------------------------------------------------
                # SHOW QUESTIONS
                # -------------------------------------------------

                for index, q in enumerate(
                    st.session_state.quiz_questions
                ):

                    question_id = q[0]
                    question_text = q[1]

                    option_a = q[2]
                    option_b = q[3]
                    option_c = q[4]
                    option_d = q[5]

                    st.write(
                        f"### Question {index + 1}"
                    )

                    st.write(question_text)

                    st.radio(
                        "Choose your answer:",
                        [
                            option_a,
                            option_b,
                            option_c,
                            option_d
                        ],
                        key=f"answer_{question_id}",
                        index=None
                    )

                    st.divider()

                if st.button(
                    "✅ Submit Quiz",
                    use_container_width=True
                ):

                    unanswered = []

                    for q in st.session_state.quiz_questions:

                        question_id = q[0]

                        answer = st.session_state.get(
                            f"answer_{question_id}"
                        )

                        if answer is None:
                            unanswered.append(question_id)

                    if unanswered:

                        st.warning(
                            "Please answer all questions before submitting."
                        )

                    else:

                        score = 0
                        answers = []

                        for q in st.session_state.quiz_questions:

                            question_id = q[0]
                            question_text = q[1]

                            option_a = q[2]
                            option_b = q[3]
                            option_c = q[4]
                            option_d = q[5]

                            correct_letter = q[6]

                            options = {
                                "A": option_a,
                                "B": option_b,
                                "C": option_c,
                                "D": option_d
                            }

                            selected_answer = st.session_state.get(
                                f"answer_{question_id}"
                            )

                            correct_answer = options[
                                correct_letter
                            ]

                            is_correct = (
                                selected_answer
                                == correct_answer
                            )

                            if is_correct:
                                score += 1

                            answers.append({
                                "question": question_text,
                                "selected": selected_answer,
                                "correct": correct_answer
                            })

                        total = len(
                            st.session_state.quiz_questions
                        )

                        percentage = (
                            score / total
                        ) * 100

                        attempt_id = save_attempt(
                            st.session_state.quiz_subject,
                            st.session_state.quiz_name,
                            score,
                            total,
                            percentage,
                            answers
                        )

                        st.session_state.last_attempt_id = attempt_id
                        st.session_state.quiz_submitted = True
                        st.session_state.quiz_started = False

                        st.rerun()

        else:

            st.info(
                "No quizzes are available for this subject."
            )


# =========================================================
# QUIZ RESULT
# =========================================================

if (
    page == "📝 Take Quiz"
    and st.session_state.quiz_submitted
    and st.session_state.last_attempt_id
):

    st.title("📊 Quiz Result")

    attempts = get_attempts()

    current_attempt = None

    for attempt in attempts:

        if attempt[0] == st.session_state.last_attempt_id:
            current_attempt = attempt
            break

    if current_attempt:

        (
            attempt_id,
            subject,
            quiz_name,
            score,
            total,
            percentage,
            date_taken
        ) = current_attempt

        st.metric(
            "Your Score",
            f"{score}/{total}"
        )

        st.metric(
            "Percentage",
            f"{percentage:.1f}%"
        )

        if percentage >= 90:

            st.success("Excellent work! 🎉")

        elif percentage >= 75:

            st.success("Good job! Keep practicing! 👍")

        elif percentage >= 50:

            st.warning("Keep reviewing your lessons. 📖")

        else:

            st.error(
                "You can improve by reviewing the questions again."
            )

        st.divider()

        st.subheader("🔎 Review Your Answers")

        answers = get_attempt_answers(
            attempt_id
        )

        for index, answer in enumerate(answers):

            question = answer[0]
            selected = answer[1]
            correct = answer[2]
            is_correct = answer[3]

            st.write(
                f"### Question {index + 1}"
            )

            st.write(question)

            if is_correct:

                st.success(
                    f"✅ Your answer: {selected}"
                )

            else:

                st.error(
                    f"❌ Your answer: {selected}"
                )

                st.info(
                    f"Correct answer: {correct}"
                )

            st.divider()

        if st.button("🔄 Take Another Quiz"):

            st.session_state.quiz_submitted = False
            st.session_state.last_attempt_id = None

            st.rerun()


# =========================================================
# CREATE QUESTION
# =========================================================

elif page == "➕ Create Question":

    st.title("➕ Create Question")

    st.write(
        "Create a multiple-choice question for your quiz."
    )

    with st.form("create_question_form"):

        subject = st.text_input(
            "Subject",
            placeholder="Example: Programming"
        )

        quiz_name = st.text_input(
            "Quiz Name",
            placeholder="Example: Python Basics"
        )

        question = st.text_area(
            "Question",
            placeholder="Enter your question here..."
        )

        col1, col2 = st.columns(2)

        with col1:

            option_a = st.text_input(
                "Option A"
            )

            option_b = st.text_input(
                "Option B"
            )

        with col2:

            option_c = st.text_input(
                "Option C"
            )

            option_d = st.text_input(
                "Option D"
            )

        correct_answer = st.selectbox(
            "Correct Answer",
            ["A", "B", "C", "D"]
        )

        submitted = st.form_submit_button(
            "💾 Save Question",
            use_container_width=True
        )

        if submitted:

            if not subject.strip():

                st.error(
                    "Please enter a subject."
                )

            elif not quiz_name.strip():

                st.error(
                    "Please enter a quiz name."
                )

            elif not question.strip():

                st.error(
                    "Please enter a question."
                )

            elif not all([
                option_a.strip(),
                option_b.strip(),
                option_c.strip(),
                option_d.strip()
            ]):

                st.error(
                    "Please fill in all four choices."
                )

            else:

                add_question(
                    subject.strip(),
                    quiz_name.strip(),
                    question.strip(),
                    option_a.strip(),
                    option_b.strip(),
                    option_c.strip(),
                    option_d.strip(),
                    correct_answer
                )

                st.success(
                    "Question successfully added! ✅"
                )


# =========================================================
# QUESTION SETS
# =========================================================

elif page == "📋 Question Sets":

    st.title("📋 Question Sets")

    questions = get_all_questions()

    if not questions:

        st.info(
            "No questions have been created yet."
        )

    else:

        subjects = get_subjects()

        selected_subject = st.selectbox(
            "Filter by Subject",
            ["All Subjects"] + subjects
        )

        if selected_subject == "All Subjects":

            filtered_questions = questions

        else:

            filtered_questions = [
                q for q in questions
                if q[1] == selected_subject
            ]

        st.write(
            f"Showing **{len(filtered_questions)}** question(s)."
        )

        for q in filtered_questions:

            (
                question_id,
                subject,
                quiz_name,
                question,
                option_a,
                option_b,
                option_c,
                option_d,
                correct_answer
            ) = q

            with st.expander(
                f"📚 {subject} | {quiz_name} | Question #{question_id}"
            ):

                st.write(
                    f"**Question:** {question}"
                )

                st.write(
                    f"A. {option_a}"
                )

                st.write(
                    f"B. {option_b}"
                )

                st.write(
                    f"C. {option_c}"
                )

                st.write(
                    f"D. {option_d}"
                )

                st.success(
                    f"Correct Answer: {correct_answer}"
                )

                if st.button(
                    "🗑️ Delete Question",
                    key=f"delete_{question_id}"
                ):

                    delete_question(question_id)

                    st.success(
                        "Question deleted."
                    )

                    st.rerun()


# =========================================================
# QUIZ HISTORY
# =========================================================

elif page == "📊 Quiz History":

    st.title("📊 Quiz History")

    attempts = get_attempts()

    if not attempts:

        st.info(
            "You have no previous quiz attempts."
        )

    else:

        st.subheader("Previous Attempts")

        for attempt in attempts:

            (
                attempt_id,
                subject,
                quiz_name,
                score,
                total,
                percentage,
                date_taken
            ) = attempt

            with st.expander(
                f"{quiz_name} | {subject} | "
                f"{score}/{total} ({percentage:.1f}%)"
            ):

                st.write(
                    f"**Subject:** {subject}"
                )

                st.write(
                    f"**Quiz:** {quiz_name}"
                )

                st.write(
                    f"**Score:** {score}/{total}"
                )

                st.write(
                    f"**Percentage:** {percentage:.1f}%"
                )

                st.write(
                    f"**Date Taken:** {date_taken}"
                )

                st.divider()

                st.write("### Answer Review")

                answers = get_attempt_answers(
                    attempt_id
                )

                for index, answer in enumerate(answers):

                    (
                        question,
                        selected,
                        correct,
                        is_correct
                    ) = answer

                    st.write(
                        f"**{index + 1}. {question}**"
                    )

                    if is_correct:

                        st.success(
                            f"✅ Your answer: {selected}"
                        )

                    else:

                        st.error(
                            f"❌ Your answer: {selected}"
                        )

                        st.info(
                            f"Correct answer: {correct}"
                        )

                    st.write("")