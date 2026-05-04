import random

class Planner:
    """
    Generates daily study plans based on user history and weaknesses.
    """
    
    @staticmethod
    def generate_daily_plan(user_profile, weak_topics, strong_topics, all_topics):
        """
        Input: 
        - user_profile (dict)
        - weak_topics (list)
        - strong_topics (list)
        - all_topics (list)
        
        Rules:
        - 1 Strong topic for confidence building
        - 1 Weak topic for improvement
        - 40 questions total (20 each)
        - 1 Revision slot (from strong topics)
        """
        
        # Pick one weak and one strong topic
        # If no weak topics yet, pick random
        target_weak = random.choice(weak_topics) if weak_topics else random.choice(all_topics)
        target_strong = random.choice(strong_topics) if strong_topics else random.choice(all_topics)
        
        # Ensure they are different if possible
        if target_weak == target_strong and len(all_topics) > 1:
            remaining = [t for t in all_topics if t != target_weak]
            target_strong = random.choice(remaining)

        plan = {
            "date": "Today",
            "targets": [
                {"topic": target_weak, "questions": 20, "type": "Focus"},
                {"topic": target_strong, "questions": 20, "type": "Practice"}
            ],
            "revision": random.choice(strong_topics) if strong_topics else "General Basics",
            "estimated_time": "120 mins"
        }
        
        return plan
