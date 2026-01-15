import base64
import unittest
from unittest.mock import Mock

import ingestion.fetch_emails as fe


class FetchEmailsTests(unittest.TestCase):

    def test_extract_text_body_plain(self):
        text = 'hello world'
        encoded = base64.urlsafe_b64encode(text.encode()).decode()
        payload = {
            'mimeType': 'multipart/alternative',
            'parts': [
                {'mimeType': 'text/plain', 'body': {'data': encoded}}
            ]
        }
        result = fe._extract_text_body(payload)
        self.assertEqual(result, text)

    def test_extract_html_body(self):
        html = '<html><body><h1>Title</h1><p>Some content</p></body></html>'
        encoded = base64.urlsafe_b64encode(html.encode()).decode()
        payload = {
            'mimeType': 'multipart/alternative',
            'parts': [
                {'mimeType': 'text/html', 'body': {'data': encoded}}
            ]
        }
        result = fe._extract_html_body(payload)
        self.assertIn('<h1>Title</h1>', result)

    def test_extract_link_from_html_tracking_and_nontracking(self):
        # tracking link encodes the real URL after /CL0/
        tracking_encoded = 'https%3A%2F%2Fexample.com%2Farticle'
        tracking_link = f'https://links.tldrnewsletter.com/CL0/{tracking_encoded}'
        nontracking = 'https://plain.example.com/page'
        mailto = 'mailto:user@example.com'
        html = f'<a href="{tracking_link}">t</a><a href="{nontracking}">n</a><a href="{mailto}">m</a>'
        results = fe._extract_link_from_html(html)
        # tracking should be decoded to the real URL and non-http/mailto should be filtered
        self.assertIn('https://example.com/article', results)
        self.assertIn(nontracking, results)
        self.assertNotIn(mailto, results)

    def test_fetch_messages_and_get_latest_newsletter_links(self):
        # Mock gmail_service to return one message id and a full message with an HTML body
        gmail_service = Mock()
        users = Mock()
        messages = Mock()
        gmail_service.users.return_value = users
        users.messages.return_value = messages

        # list() request
        list_request = Mock()
        list_request.execute.return_value = {'messages': [{'id': 'msg1'}]}
        messages.list.return_value = list_request
        messages.list_next.return_value = None

        # prepare html with a tracking link that decodes to example.com and one that decodes to an unallowed domain
        tracking_allowed = 'https%3A%2F%2Fexample.com%2Farticle'
        tracking_blocked = 'https%3A%2F%2Flinks.tldrnewsletter.com%2Fpromo'
        html = f'<a href="https://links.tldrnewsletter.com/CL0/{tracking_allowed}">a</a>'
        html += f'<a href="https://links.tldrnewsletter.com/CL0/{tracking_blocked}">b</a>'
        encoded_html = base64.urlsafe_b64encode(html.encode()).decode()

        full_message = {'payload': {'mimeType': 'multipart/alternative', 'parts': [
            {'mimeType': 'text/html', 'body': {'data': encoded_html}}
        ]}}

        get_request = Mock()
        get_request.execute.return_value = full_message
        messages.get.return_value = get_request

        links = fe.get_latest_newsletter_links(gmail_service, 'dan@tldrnewsletter.com')
        # should include example.com link and exclude links.tldrnewsletter.com
        self.assertTrue(any('example.com/article' in l for l in links))
        self.assertFalse(any('links.tldrnewsletter.com' in l for l in links))


if __name__ == '__main__':
    unittest.main()
