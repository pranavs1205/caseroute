"""Credential parsing and AnyAPI compatibility checks without network access."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from anyapi_smoke import load_key, load_setting
from llm import Decision, LLMUnavailable, SearchPlan, generate


class AnyAPIIntegration(unittest.TestCase):
    def test_dotenv_is_parsed_without_execution(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {}, clear=True):
            path = Path(directory) / '.env'
            path.write_text('UNRELATED=ignore\nexport ANY_API_KEY="test-only-value" # comment\n', encoding='utf-8')
            self.assertEqual(load_key(path), 'test-only-value')
            with patch.dict(os.environ, {'ANYAPI_API_KEY': 'environment-value'}):
                self.assertEqual(load_key(path), 'environment-value')
            path.write_text('ANY_API_KEY=$(never-execute-this)\n', encoding='utf-8')
            self.assertEqual(load_key(path), '$(never-execute-this)')

    @patch('llm.load_key', return_value='test-only-value')
    @patch('llm.configuration', return_value={'provider':'anyapi', 'model':'fixture-model', 'configured':True})
    def test_minimal_completion_body_and_validated_usage_receipt(self, config, key):
        payload = {'model':'fixture-returned-model', 'choices':[{'message':{'content':'```json\n{"terms":["pyspark"],"version":null}\n```'}}],
                   'usage':{'prompt_tokens':10,'completion_tokens':8,'total_tokens':18}}
        trace = []
        with patch('llm.request_json', return_value=(200, {}, payload)) as request:
            value = generate(SearchPlan, 'Extract search terms', {'report':'pyspark error'}, trace, 'interpret_report')
        self.assertEqual(value.terms, ['pyspark'])
        args = request.call_args.args
        self.assertEqual(args[:3], ('POST', '/v1/chat/completions', 'test-only-value'))
        self.assertEqual(set(args[3]), {'model', 'messages'})
        self.assertEqual(trace[0]['provider'], 'anyapi')
        self.assertEqual(trace[0]['returned_model'], 'fixture-returned-model')
        self.assertEqual(trace[0]['usage']['total_tokens'], 18)
        self.assertNotIn('test-only-value', json.dumps(trace))

    @patch('llm.load_key', return_value='test-only-value')
    @patch('llm.configuration', return_value={'provider':'anyapi', 'model':'fixture-model', 'configured':True})
    def test_provider_errors_do_not_echo_secret_or_fall_back(self, config, key):
        for status in (401, 403, 429):
            with patch('llm.request_json', return_value=(status, {}, {'error':{'message':'test-only-value'}})) as request:
                with self.assertRaises(LLMUnavailable) as raised:
                    generate(SearchPlan, 'Extract terms', {}, [], 'interpret_report')
                self.assertNotIn('test-only-value', str(raised.exception))
                self.assertIn(str(status), str(raised.exception))
                self.assertEqual(request.call_count, 1)

    @patch('llm.load_key', return_value='test-only-value')
    @patch('llm.configuration', return_value={'provider':'anyapi', 'model':'fixture-model', 'configured':True})
    def test_invalid_model_json_is_rejected(self, config, key):
        with patch('llm.request_json', return_value=(200, {}, {'choices':[{'message':{'content':'I think this is fixed'}}]})):
            with self.assertRaises(LLMUnavailable):
                generate(Decision, 'Select step', {}, [], 'choose_next_step')


if __name__ == '__main__':
    unittest.main()
