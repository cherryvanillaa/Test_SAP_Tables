import unittest
import asyncio
from unittest.mock import patch, MagicMock
from sap_tables_agent_web import SAPHanaAgent

class TestSAPHanaAgent(unittest.TestCase):
    def setUp(self):
        self.agent = SAPHanaAgent()
        self.loop = asyncio.get_event_loop()

    def tearDown(self):
        self.loop.run_until_complete(self.agent.close())

    @patch('aiohttp.ClientSession.get')
    def test_get_table_list(self, mock_get):
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.text = asyncio.coroutine(lambda: """
            <html>
                <body>
                    <a href="/abap/tabl/MARA">MARA</a>
                    <a href="/abap/tabl/MARC">MARC</a>
                </body>
            </html>
        """)()
        mock_get.return_value.__aenter__.return_value = mock_response

        tables = self.loop.run_until_complete(self.agent.get_table_list(limit=2))
        self.assertEqual(len(tables), 2)
        self.assertEqual(tables[0]['name'], 'MARA')
        self.assertEqual(tables[1]['name'], 'MARC')

    @patch('aiohttp.ClientSession.get')
    def test_get_table_fields(self, mock_get):
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.text = asyncio.coroutine(lambda: """
            <html>
                <body>
                    <table class="table-fields">
                        <tr>
                            <th>Field</th>
                            <th>Key</th>
                            <th>Type</th>
                            <th>Length</th>
                            <th>Description</th>
                        </tr>
                        <tr>
                            <td>MATNR</td>
                            <td>X</td>
                            <td>CHAR</td>
                            <td>18</td>
                            <td>Material Number</td>
                        </tr>
                    </table>
                </body>
            </html>
        """)()
        mock_get.return_value.__aenter__.return_value = mock_response

        fields = self.loop.run_until_complete(
            self.agent.get_table_fields('https://example.com/table/MARA')
        )
        self.assertEqual(len(fields), 1)
        self.assertEqual(fields[0]['name'], 'MATNR')
        self.assertTrue(fields[0]['key'])
        self.assertEqual(fields[0]['type'], 'CHAR')

if __name__ == '__main__':
    unittest.main() 