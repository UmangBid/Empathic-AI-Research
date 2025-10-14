"""
Random Assignment Module
Handles random assignment of participants to bot types with equal distribution.
"""

import random
from typing import List, Dict
from src.database.db_manager import DatabaseManager


class RandomAssignment:
    """
    Manages random assignment of participants to bot types.
    Ensures equal distribution across all bot types.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize random assignment system.
        
        Args:
            db_manager: DatabaseManager instance to check current distribution
        """
        self.db_manager = db_manager
        self.bot_types = ['emotional', 'cognitive', 'motivational', 'neutral']
    
    
    def get_bot_distribution(self) -> Dict[str, int]:
        """
        Get current count of participants assigned to each bot type.
        
        Returns:
            Dictionary with bot types as keys and counts as values
        """
        stats = self.db_manager.get_statistics()
        return stats['bot_distribution']
    
    
    def assign_bot_type(self, method: str = "equal_distribution") -> str:
        """
        Assign a bot type to a new participant.
        
        Args:
            method: Assignment method
                - "equal_distribution": Assigns to bot type with fewest participants
                - "random": Completely random assignment
                - "sequential": Rotates through bot types in order
                
        Returns:
            Assigned bot type string
        """
        if method == "equal_distribution":
            return self._assign_equal_distribution()
        elif method == "random":
            return self._assign_random()
        elif method == "sequential":
            return self._assign_sequential()
        else:
            # Default to equal distribution
            return self._assign_equal_distribution()
    
    
    def _assign_equal_distribution(self) -> str:
        """
        Assign bot type ensuring equal distribution.
        Chooses bot type with fewest current participants.
        If tied, randomly chooses among the tied options.
        
        Returns:
            Bot type with fewest participants
        """
        # Get current distribution
        distribution = self.get_bot_distribution()
        
        # Find minimum count
        min_count = min(distribution.values())
        
        # Get all bot types with minimum count
        bot_types_with_min = [bot for bot, count in distribution.items() if count == min_count]
        
        # Randomly choose among tied options
        assigned_bot = random.choice(bot_types_with_min)
        
        print(f"✓ Assigned bot type: {assigned_bot}")
        print(f"  Current distribution: {distribution}")
        
        return assigned_bot
    
    
    def _assign_random(self) -> str:
        """
        Completely random assignment (no balancing).
        
        Returns:
            Randomly chosen bot type
        """
        assigned_bot = random.choice(self.bot_types)
        print(f"✓ Randomly assigned bot type: {assigned_bot}")
        return assigned_bot
    
    
    def _assign_sequential(self) -> str:
        """
        Sequential assignment - rotates through bot types.
        Pattern: emotional -> cognitive -> motivational -> neutral -> repeat
        
        Returns:
            Next bot type in sequence
        """
        # Get total participants
        stats = self.db_manager.get_statistics()
        total_participants = stats['total_participants']
        
        # Determine next in sequence
        index = total_participants % len(self.bot_types)
        assigned_bot = self.bot_types[index]
        
        print(f"✓ Sequential assignment: {assigned_bot}")
        return assigned_bot
    
    
    def get_assignment_report(self) -> Dict:
        """
        Get detailed report on current assignment distribution.
        
        Returns:
            Dictionary with distribution statistics
        """
        distribution = self.get_bot_distribution()
        total = sum(distribution.values())
        
        report = {
            'total_participants': total,
            'distribution': distribution,
            'percentages': {}
        }
        
        # Calculate percentages
        if total > 0:
            for bot_type, count in distribution.items():
                percentage = (count / total) * 100
                report['percentages'][bot_type] = round(percentage, 2)
        
        return report
    
    
    def print_distribution_report(self):
        """
        Print a formatted distribution report to console.
        """
        report = self.get_assignment_report()
        
        print("\n" + "="*50)
        print("PARTICIPANT DISTRIBUTION REPORT")
        print("="*50)
        print(f"Total Participants: {report['total_participants']}")
        print("\nDistribution by Bot Type:")
        print("-"*50)
        
        for bot_type in self.bot_types:
            count = report['distribution'].get(bot_type, 0)
            percentage = report['percentages'].get(bot_type, 0)
            print(f"  {bot_type.capitalize():15} : {count:3} ({percentage:5.1f}%)")
        
        print("="*50 + "\n")