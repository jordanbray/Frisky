import responses

from frisky.responses import Image
from frisky.test import FriskyTestCase
from plugins.meme import MemePlugin

meme_list = '''
{
   "success":true,
   "data":{
      "memes":[
         {
            "id":"181913649",
            "name":"Drake Hotline Bling",
            "url":"https://i.imgflip.com/30b1gx.jpg",
            "width":1200,
            "height":1200,
            "box_count":2
         },
         {
            "id":"112126428",
            "name":"Distracted Boyfriend",
            "url":"https://i.imgflip.com/1ur9b0.jpg",
            "width":1200,
            "height":800,
            "box_count":3
         },
         {
            "id":"87743020",
            "name":"Two Buttons",
            "url":"https://i.imgflip.com/1g8my4.jpg",
            "width":600,
            "height":908,
            "box_count":2
         }
      ]
   }
}
'''.strip()


class MemeTestCase(FriskyTestCase):

    def test_only_meme(self):
        with responses.RequestsMock() as rm:
            rm.add('GET', MemePlugin.GET_MEMES_URL, body=meme_list)

            reply = self.send_message('?meme')
            self.assertEqual(reply, '"Drake Hotline Bling", "Distracted Boyfriend", "Two Buttons"')

    def test_listing_failure_with_args(self):
        with responses.RequestsMock() as rm:
            rm.add('GET', MemePlugin.GET_MEMES_URL, body='''
            {
                "success": false
            }
            '''.strip())
            reply = self.send_message('?meme "" "" ""')
            self.assertEqual('NO MEMES', reply)

    def test_listing_failure(self):
        with responses.RequestsMock() as rm:
            rm.add('GET', MemePlugin.GET_MEMES_URL, body='''
            {
                "success": false
            }
            '''.strip())
            reply = self.send_message('?meme')
            self.assertEqual('NO MEMES', reply)

    def test_success(self):
        with responses.RequestsMock() as rm:
            rm.add('GET', MemePlugin.GET_MEMES_URL, body=meme_list)
            rm.add('POST', MemePlugin.CAPTION_IMAGE_URL, body='''
            {
                "success": true,
                "data": {
                    "url": "https://i.imgflip.com/123abc.jpg",
                    "page_url": "https://imgflip.com/i/123abc"
                }
            }
            '''.strip())
            reply = self.send_message('?meme "Drake Hotline Bling" "One Does Not Simply" "Mock Http Requests"')
            self.assertEqual(rm.calls[1].request.body,
                             'template_id=181913649&username=&password=&text0=One+Does+Not+Simply&' +
                             'text1=Mock+Http+Requests')
            self.assertIsInstance(reply, Image)
            self.assertEqual(reply.url, 'https://i.imgflip.com/123abc.jpg')

    def test_nonexistant_meme(self):
        with responses.RequestsMock() as rm:
            rm.add('GET', MemePlugin.GET_MEMES_URL, body=meme_list)
            reply = self.send_message('?meme "420noscopeyolo" "foo" "bar"')
            self.assertEqual('NO SUCH MEME', reply)

    def test_plugin_returns_error_message(self):
        with responses.RequestsMock() as rm:
            rm.add('GET', MemePlugin.GET_MEMES_URL, body=meme_list)
            rm.add('POST', MemePlugin.CAPTION_IMAGE_URL, body='''
            {
                "success": false,
                "error_message": "YA DONE FUCKED UP LADDIE"
            }
            '''.strip())
            reply = self.send_message('?meme "Drake Hotline Bling" "foo" "bar"')
            self.assertEqual('YA DONE FUCKED UP LADDIE', reply)

    def test_improper_usage(self):
        reply = self.send_message('?meme 1 2 3 4')
        self.assertEqual('Usage: `?meme <meme_id> <text0> <text1>`', reply)

    def test_alias_creation(self):
        reply = self.send_message('?memealias goodnews 123456')
        self.assertEqual('Ok, added goodnews', reply)
        reply = self.send_message('?memealias list')
        self.assertEqual('goodnews', reply)

    def test_alias_creation_fails_with_noninteger(self):
        reply = self.send_message('?memealias goodnews asdf')
        self.assertEqual('Usage: `?memealias <alias> <id>`', reply)
        reply = self.send_message('?memealias list')
        self.assertEqual('', reply)

    def test_duplicate_creation(self):
        reply = self.send_message('?memealias goodnews 123456')
        self.assertEqual('Ok, added goodnews', reply)
        reply = self.send_message('?memealias goodnews 123456')
        self.assertEqual('Error: alias already exists', reply)

    def test_memealias_usage_text(self):
        reply = self.send_message('?memealias goodnews 123456 asdff')
        self.assertEqual('Usage: `?memealias <alias> <id>` or `?memealias list`', reply)
        reply = self.send_message('?memealias')
        self.assertEqual('Usage: `?memealias <alias> <id>` or `?memealias list`', reply)

    def test_alias_with_spaces(self):
        reply = self.send_message('?memealias goodnews 123456')
        self.assertEqual('Ok, added goodnews', reply)
        with responses.RequestsMock() as rm:
            rm.add('POST', MemePlugin.CAPTION_IMAGE_URL, body='''
            {
                "success": true,
                "data": {
                    "url": "https://i.imgflip.com/123abc.jpg",
                    "page_url": "https://imgflip.com/i/123abc"
                }
            }
            '''.strip())
            reply = self.send_message('?meme goodnews "One Does Not Simply" "Mock Http Requests"')
            self.assertEqual(rm.calls[0].request.body,
                             'template_id=123456&username=&password=&text0=One+Does+Not+Simply&' +
                             'text1=Mock+Http+Requests')
            self.assertIsInstance(reply, Image)
            self.assertEqual(reply.url, 'https://i.imgflip.com/123abc.jpg')
