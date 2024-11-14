import unittest
from my_project.services.database import connect_to_database

class TestServices(unittest.TestCase):

    def test_database_connection(self):
        conn = connect_to_database()
        self.assertIsNotNone(conn)

if __name__ == '__main__':
    unittest.main()
