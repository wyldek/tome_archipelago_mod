from .bases import ToMETestBase

class TestDefaultWorld(ToMETestBase):
    def test_exact_accounting(self):
        self.assertEqual(len(self.world.build.pool), len(self.world.build.locations))

class TestSmallWorld(ToMETestBase):
    options = {"class_tree_count": 2, "generic_tree_count": 2}

class TestNoStarters(ToMETestBase):
    options = {"starting_ranks": 0}
