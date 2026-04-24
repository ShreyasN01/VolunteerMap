import 'dart:io';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import '../../services/api_service.dart';
import 'submit_survey_screen.dart';

class OcrUploadScreen extends StatefulWidget {
  const OcrUploadScreen({super.key});

  @override
  State<OcrUploadScreen> createState() => _OcrUploadScreenState();
}

class _OcrUploadScreenState extends State<OcrUploadScreen> {
  File? _image;
  bool _isLoading = false;
  final ImagePicker _picker = ImagePicker();

  Future<void> _pickImage(ImageSource source) async {
    final XFile? pickedFile = await _picker.pickImage(source: source);
    if (pickedFile != null) {
      setState(() => _image = File(pickedFile.path));
    }
  }

  Future<void> _extractData() async {
    if (_image == null) return;
    setState(() => _isLoading = true);
    
    try {
      final results = await ApiService().uploadOcrImage(_image!);
      if (mounted) {
        if (results != null) {
          Navigator.pushReplacement(
            context,
            MaterialPageRoute(
              builder: (_) => SubmitSurveyScreen(initialData: results),
            ),
          );
        } else {
          ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('OCR Failed to extract data.')));
        }
      }
    } finally {
      setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('OCR Survey Digitisation')),
      body: _isLoading 
        ? const Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                CircularProgressIndicator(),
                SizedBox(height: 16),
                Text('Gemini is analysing the document...', style: TextStyle(fontStyle: FontStyle.italic)),
              ],
            ),
          )
        : Padding(
            padding: const EdgeInsets.all(24.0),
            child: Column(
              children: [
                Row(
                  children: [
                    Expanded(
                      child: InkWell(
                        onTap: () => _pickImage(ImageSource.camera),
                        child: _buildActionCard(Icons.camera_alt, 'Take Photo', Colors.teal),
                      ),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: InkWell(
                        onTap: () => _pickImage(ImageSource.gallery),
                        child: _buildActionCard(Icons.photo_library, 'Upload Gallery', Colors.blue),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 32),
                if (_image != null) ...[
                  Expanded(
                    child: Container(
                      width: double.infinity,
                      decoration: BoxDecoration(
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: Colors.grey[300]!),
                      ),
                      child: ClipRRect(
                        borderRadius: BorderRadius.circular(12),
                        child: Image.file(_image!, fit: BoxFit.cover),
                      ),
                    ),
                  ),
                  const SizedBox(height: 32),
                  ElevatedButton(
                    onPressed: _extractData,
                    style: ElevatedButton.styleFrom(
                      minimumSize: const Size(double.infinity, 56),
                      backgroundColor: Colors.teal,
                      foregroundColor: Colors.white,
                    ),
                    child: const Text('Extract Survey Data'),
                  ),
                ] else
                  const Expanded(
                    child: Center(
                      child: Text('Select an image to start OCR extraction', style: TextStyle(color: Colors.grey)),
                    ),
                  ),
              ],
            ),
          ),
    );
  }

  Widget _buildActionCard(IconData icon, String label, Color color) {
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: color.withValues(alpha: 0.3)),
      ),
      child: Column(
        children: [
          Icon(icon, color: color, size: 40),
          const SizedBox(height: 12),
          Text(label, style: TextStyle(color: color, fontWeight: FontWeight.bold)),
        ],
      ),
    );
  }
}
