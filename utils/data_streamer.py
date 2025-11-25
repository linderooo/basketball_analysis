import json
import os

class TacticalDataStreamer:
    def __init__(self, output_path):
        self.output_path = output_path
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        # Clear existing file
        with open(self.output_path, 'w') as f:
            pass

    def write_frame(self, frame_num, tactical_player_positions, player_assignment, ball_acquisition):
        """
        Writes a single frame of data to the JSONL file.
        """
        frame_data = {
            "frame": frame_num,
            "players": [],
            "ball_owner": int(ball_acquisition[frame_num]) if ball_acquisition and frame_num < len(ball_acquisition) else -1
        }

        if tactical_player_positions and frame_num < len(tactical_player_positions):
            positions = tactical_player_positions[frame_num]
            assignments = player_assignment[frame_num] if player_assignment and frame_num < len(player_assignment) else {}

            for player_id, pos in positions.items():
                team_id = assignments.get(player_id, 1)
                frame_data["players"].append({
                    "id": int(player_id),
                    "x": float(pos[0]),
                    "y": float(pos[1]),
                    "team": int(team_id)
                })

        with open(self.output_path, 'a') as f:
            f.write(json.dumps(frame_data) + '\n')
