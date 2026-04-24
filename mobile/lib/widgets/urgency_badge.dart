import 'package:flutter/material.dart';

class UrgencyBadge extends StatelessWidget {
  final double score;

  const UrgencyBadge({super.key, required this.score});

  @override
  Widget build(BuildContext context) {
    Color bgColor;
    if (score > 70) {
      bgColor = Colors.red;
    } else if (score > 40) {
      bgColor = Colors.orange;
    } else {
      bgColor = Colors.green;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Text(
        score.toInt().toString(),
        style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 12),
      ),
    );
  }
}
