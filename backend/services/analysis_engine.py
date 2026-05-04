class AnalysisEngine:
    """
    Analyzes quiz attempts to classify mistakes and detect guesses.
    """
    
    @staticmethod
    def classify_mistake(is_correct, time_taken, avg_time_topic, difficulty_level):
        """
        Logic for mistake classification:
        - Guess: Correct but time < 15% of avg
        - Conceptual: Wrong and time > 80% of avg
        - Calculation/Careless: Wrong and time < 50% of avg
        - Time Inefficiency: Correct but time > 150% of avg
        """
        if is_correct:
            if time_taken < avg_time_topic * 0.15:
                return "Guess"
            elif time_taken > avg_time_topic * 1.5:
                return "Time Inefficiency"
            else:
                return "Mastered"
        else:
            if time_taken > avg_time_topic * 0.8:
                return "Conceptual Mistake"
            elif time_taken < avg_time_topic * 0.5:
                return "Calculation/Careless Mistake"
            else:
                return "General Error"

    @staticmethod
    def calculate_xp(is_correct, time_taken, avg_time_topic, difficulty_level):
        """
        XP Calculation:
        - Base XP based on difficulty: 10, 20, 30, 40, 50
        - Speed multiplier: 1.5x if time < 50% avg, 0.5x if time > 150% avg
        """
        base_xp = difficulty_level * 10
        if not is_correct:
            return 5 # Consolation XP
        
        multiplier = 1.0
        if time_taken < avg_time_topic * 0.5:
            multiplier = 1.5
        elif time_taken > avg_time_topic * 1.5:
            multiplier = 0.5
            
        return int(base_xp * multiplier)
