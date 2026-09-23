from dataclasses import dataclass
from Options import Range, Choice, DefaultOnToggle, PerGameCommonOptions

class ClassTreeCount(Range):
    """Number of randomly chosen class trees. Combat Training is separate and does not consume this count."""
    display_name = "Random Class Tree Count"
    range_start = 1
    range_end = 20
    default = 6

class GenericTreeCount(Range):
    """Number of randomly chosen generic trees in addition to mandatory Combat Training."""
    display_name = "Random Generic Tree Count"
    range_start = 0
    range_end = 20
    default = 4

class ProdigyCount(Range):
    """Distinct specific prodigies, granted automatically on receipt. Some prodigies add their own talent trees."""
    display_name = "Prodigy Count"
    range_start = 0
    range_end = 20
    default = 5

class StartingRanks(Range):
    """Ranks of one seed-selected offensive talent, removed from the shuffled pool."""
    display_name = "Starting Talent Ranks"
    range_start = 0
    range_end = 2
    default = 2

class LevelCeiling(Range):
    """Last scheduled advancement level. Enabled world checks consume the location budget first; remaining checks are distributed across these levels."""
    display_name = "Advancement Level Ceiling"
    range_start = 10
    range_end = 50
    default = 40

class ZoneExplorationChecks(DefaultOnToggle):
    """Add curated dungeon/campaign zone-entry checks. Enabled checks replace level-up checks rather than increasing the item pool."""
    display_name = "Zone Exploration Checks"

class QuestChecks(Choice):
    """Add deterministic major quest milestones, optionally including the four Tier-2 zone objectives."""
    display_name = "Quest Checks"
    option_none = 0
    option_major = 1
    option_major_and_zone = 2
    default = 2

class ShopChecks(Choice):
    """Paid Archipelago parcels in ordinary unrestricted-town merchants. Non-progression parcels may hold useful/filler/trap items, but never progression."""
    display_name = "Paid Shop Checks"
    option_off = 0
    option_non_progression = 1
    default = 1

class ShopChecksPerStore(Range):
    """Paid Archipelago parcel checks added to each eligible ordinary merchant when shop checks are enabled."""
    display_name = "Shop Checks Per Store"
    range_start = 1
    range_end = 3
    default = 3

class EarlyLevelMax(Range):
    """Minimum early-safe advancement cutoff. Generation extends it only if needed to fit this ToME world's early-rank requests. Level 1 has no advancement check."""
    display_name = "Early Level Check Minimum"
    range_start = 3
    range_end = 20
    default = 10

class T1T2BossPriority(DefaultOnToggle):
    """Mark the ten standard Tier-1/Tier-2 dungeon guardians as Archipelago PRIORITY locations."""
    display_name = "Tier 1/2 Boss Priority"

@dataclass
class ToMEOptions(PerGameCommonOptions):
    class_tree_count: ClassTreeCount
    generic_tree_count: GenericTreeCount
    prodigy_count: ProdigyCount
    starting_ranks: StartingRanks
    level_ceiling: LevelCeiling
    zone_exploration_checks: ZoneExplorationChecks
    quest_checks: QuestChecks
    shop_checks: ShopChecks
    shop_checks_per_store: ShopChecksPerStore
    early_level_max: EarlyLevelMax
    t1_t2_boss_priority: T1T2BossPriority
