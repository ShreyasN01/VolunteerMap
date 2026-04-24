import 'package:flutter/material.dart';
import '../models/match_result.dart';

class MatchResultCard extends StatelessWidget {
  final MatchResult match;

  const MatchResultCard({super.key, required this.match});

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 16),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                CircleAvatar(
                  backgroundColor: _getAvatarColor(match.volunteerName),
                  child: Text(match.volunteerName[0], style: const TextStyle(color: Colors.white)),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(match.volunteerName, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                      Text(match.needCategory.toUpperCase(), style: const TextStyle(fontSize: 12, color: Colors.grey, fontWeight: FontWeight.bold)),
                    ],
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: match.priorityColor.withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    match.priority,
                    style: TextStyle(color: match.priorityColor, fontSize: 10, fontWeight: FontWeight.bold),
                  ),
                ),
              ],
            ),
            const Divider(height: 24),
            const Text('Match Reason:', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Colors.grey)),
            const SizedBox(height: 4),
            Text(
              match.matchReason,
              style: const TextStyle(fontStyle: FontStyle.italic, fontSize: 13),
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                _buildChip(Icons.straighten, '${match.distance.toStringAsFixed(1)} km', Colors.blue),
                const SizedBox(width: 8),
                _buildChip(Icons.star, '${(match.matchScore * 100).toInt()}% Match', Colors.orange),
                const Spacer(),
                TextButton(onPressed: () {}, child: const Text('View Need')),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildChip(IconData icon, String label, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(color: color.withValues(alpha: 0.1), borderRadius: BorderRadius.circular(8)),
      child: Row(
        children: [
          Icon(icon, size: 12, color: color),
          const SizedBox(width: 4),
          Text(label, style: TextStyle(color: color, fontSize: 10, fontWeight: FontWeight.bold)),
        ],
      ),
    );
  }

  Color _getAvatarColor(String name) {
    final int hash = name.hashCode;
    final List<Color> colors = [Colors.teal, Colors.blue, Colors.purple, Colors.orange, Colors.indigo];
    return colors[hash.abs() % colors.length];
  }
}
