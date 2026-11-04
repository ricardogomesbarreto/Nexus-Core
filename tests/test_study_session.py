"""Testes de sessão local sem persistência nem chamadas externas."""
import unittest

from nexus.study_session import StudySession


TEXT = (
    "A fotossíntese transforma energia luminosa em energia química. "
    "Os computadores utilizam componentes eletrônicos para processar informações."
)


class StudySessionTests(unittest.TestCase):
    def test_sequence_score_and_completion(self):
        session = StudySession.from_text(TEXT, limit=2)
        self.assertEqual(len(session.questions), 2)
        self.assertFalse(session.completed)
        first = session.next_question()
        attempt = session.submit(first.expected_answer.upper())
        self.assertTrue(attempt.correct)
        self.assertEqual(session.score, (1, 1))
        session.submit("resposta incorreta")
        self.assertTrue(session.completed)
        self.assertEqual(session.score, (1, 2))
        self.assertIsNone(session.next_question())
        with self.assertRaises(ValueError):
            session.submit("extra")

    def test_empty_and_limits(self):
        session = StudySession.from_text("")
        self.assertTrue(session.completed)
        with self.assertRaises(ValueError):
            session.submit("texto")
        session = StudySession.from_text(TEXT)
        with self.assertRaises(TypeError):
            session.submit(None)
        with self.assertRaises(ValueError):
            session.submit("x" * 1001)
        self.assertEqual(session.score, (0, 0))


if __name__ == "__main__":
    unittest.main()
