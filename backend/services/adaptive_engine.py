class AdaptiveEngine:
    """
    Handles real-time difficulty adjustment based on user performance.
    Difficulty levels: 1 (Easy) to 5 (Hard)
    """

    @staticmethod
    def adjust_difficulty(current_difficulty, is_correct, time_taken, avg_time_topic):
        """
        Logic:
        - Correct + Fast (< 50% avg) -> +2 levels (max 5)
        - Correct + Normal -> +1 level (max 5)
        - Wrong + Slow (> 100% avg) -> -1 level (min 1)
        - Wrong + Fast -> -2 levels (min 1) (Indicates high speed but low accuracy/guessing)
        """
        new_difficulty = current_difficulty

        if is_correct:
            if time_taken < avg_time_topic * 0.5:
                new_difficulty += 2
            else:
                new_difficulty += 1
        else:
            if time_taken < avg_time_topic * 0.5:
                new_difficulty -= 2
            else:
                new_difficulty -= 1

        # Clamp values
        return max(1, min(5, new_difficulty))

    @staticmethod
    def select_next_question(questions_df, topic, target_difficulty):
        """
        Selects a question from the dataset matching the topic and difficulty.
        """
        # Map target_difficulty (1-5) to Easy/Medium/Hard
        if target_difficulty <= 2:
            diff_label = "Easy"
        elif target_difficulty == 3:
            diff_label = "Medium"
        else:
            diff_label = "Hard"

        filtered = questions_df[
            (questions_df["topic"] == topic) & 
            (questions_df["difficulty"] == diff_label)
        ]
        
        if filtered.empty:
            # Fallback to any question in topic
            filtered = questions_df[questions_df["topic"] == topic]
        
        if filtered.empty:
            return None
            
        return filtered.sample(1).to_dict('records')[0]
