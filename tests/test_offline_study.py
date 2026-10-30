"""Testes sem rede, banco, Ollama ou interface gráfica."""
import unittest

from nexus_core.offline_study import generate_cloze_questions, check_exact_answer


class OfflineStudyTests(unittest.TestCase):
    def test_source_grounded_question(self):
        source = "A fotossíntese transforma energia luminosa em energia química."
        questions = generate_cloze_questions(source)
        self.assertEqual(len(questions), 1)
        self.assertEqual(questions[0].source_excerpt, source)
        self.assertIn("_____", questions[0].prompt)
        self.assertTrue(check_exact_answer(questions[0], questions[0].expected_answer.upper()))

    def test_limits_and_empty(self):
        self.assertEqual(generate_cloze_questions(""), [])
        with self.assertRaises(ValueError):
            generate_cloze_questions("a" * 16001)
        with self.assertRaises(ValueError):
            generate_cloze_questions("Texto válido.", limit=0)
        with self.assertRaises(ValueError):
            generate_cloze_questions("Texto válido.", limit=True)

    def test_no_semantic_grading(self):
        q = generate_cloze_questions("O computador utiliza componentes eletrônicos para processar informações.")[0]
        self.assertFalse(check_exact_answer(q, "uma resposta diferente"))


if __name__ == "__main__":
    unittest.main()
