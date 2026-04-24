import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../providers/survey_provider.dart';
import '../../services/location_service.dart';
import '../../widgets/urgency_badge.dart';

class SubmitSurveyScreen extends StatefulWidget {
  final Map<String, dynamic>? initialData;
  const SubmitSurveyScreen({super.key, this.initialData});

  @override
  State<SubmitSurveyScreen> createState() => _SubmitSurveyScreenState();
}

class _SubmitSurveyScreenState extends State<SubmitSurveyScreen> {
  int _currentStep = 0;
  final _formKey = GlobalKey<FormState>();
  
  // Step 1: Location
  double? _lat, _lng;
  String _district = 'Pune';
  final TextEditingController _stateController = TextEditingController(text: 'Maharashtra');

  // Step 2: Need Details
  String _category = 'Healthcare';
  final TextEditingController _descriptionController = TextEditingController();
  double _severity = 3.0;
  final TextEditingController _countController = TextEditingController();

  final List<String> _districts = [
    'Ahmednagar', 'Akola', 'Amravati', 'Aurangabad', 'Beed', 'Bhandara', 'Buldhana', 
    'Chandrapur', 'Dhule', 'Gadchiroli', 'Gondia', 'Hingoli', 'Jalgaon', 'Jalna', 
    'Kolhapur', 'Latur', 'Mumbai City', 'Mumbai Suburban', 'Nagpur', 'Nanded', 
    'Nandurbar', 'Nashik', 'Osmanabad', 'Palghar', 'Parbhani', 'Pune', 'Raigad', 
    'Ratnagiri', 'Sangli', 'Satara', 'Sindhudurg', 'Solapur', 'Thane', 'Wardha', 
    'Washim', 'Yavatmal'
  ];

  @override
  void initState() {
    super.initState();
    if (widget.initialData != null) {
      _category = widget.initialData!['category'] ?? 'Healthcare';
      _descriptionController.text = widget.initialData!['description'] ?? '';
      _district = widget.initialData!['district'] ?? 'Pune';
    }
  }

  void _submit() async {
    final data = {
      'category': _category.toLowerCase(),
      'description': _descriptionController.text,
      'severity': _severity.toInt(),
      'affected_count': int.tryParse(_countController.text) ?? 10,
      'district': _district,
      'state': _stateController.text,
      'location': {'latitude': _lat ?? 19.0760, 'longitude': _lng ?? 72.8777},
      'source': 'mobile_app',
    };

    final success = await context.read<SurveyProvider>().submitSurvey(data);
    if (mounted) {
      if (success) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Survey submitted successfully!')));
        Navigator.pop(context);
      } else {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Failed to submit survey.')));
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Submit Survey')),
      body: Form(
        key: _formKey,
        child: Stepper(
          currentStep: _currentStep,
          onStepContinue: () {
            if (_currentStep < 2) {
              setState(() => _currentStep++);
            } else {
              _submit();
            }
          },
          onStepCancel: () {
            if (_currentStep > 0) setState(() => _currentStep--);
          },
          steps: [
            Step(
              title: const Text('Location'),
              isActive: _currentStep >= 0,
              content: Column(
                children: [
                  ElevatedButton.icon(
                    onPressed: () async {
                      final pos = await LocationService.getCurrentPosition();
                      if (pos != null) {
                        setState(() {
                          _lat = pos.latitude;
                          _lng = pos.longitude;
                        });
                        final d = await LocationService.getDistrictFromCoords(pos.latitude, pos.longitude);
                        if (d != 'Unknown') setState(() => _district = d);
                      }
                    },
                    icon: const Icon(Icons.my_location),
                    label: const Text('Detect my location'),
                  ),
                  const SizedBox(height: 16),
                  DropdownButtonFormField<String>(
                    value: _district,
                    items: _districts.map((d) => DropdownMenuItem(value: d, child: Text(d))).toList(),
                    onChanged: (v) => setState(() => _district = v!),
                    decoration: const InputDecoration(labelText: 'District', border: OutlineInputBorder()),
                  ),
                  const SizedBox(height: 16),
                  TextFormField(
                    controller: _stateController,
                    decoration: const InputDecoration(labelText: 'State', border: OutlineInputBorder()),
                    readOnly: true,
                  ),
                ],
              ),
            ),
            Step(
              title: const Text('Need Details'),
              isActive: _currentStep >= 1,
              content: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Category', style: TextStyle(fontWeight: FontWeight.bold)),
                  const SizedBox(height: 8),
                  Wrap(
                    spacing: 8,
                    children: ['Healthcare', 'Food', 'Education', 'Sanitation', 'Employment'].map((cat) {
                      return ChoiceChip(
                        label: Text(cat),
                        selected: _category == cat,
                        onSelected: (val) => setState(() => _category = cat),
                      );
                    }).toList(),
                  ),
                  const SizedBox(height: 16),
                  TextFormField(
                    controller: _descriptionController,
                    maxLines: 3,
                    maxLength: 500,
                    decoration: const InputDecoration(labelText: 'Description', border: OutlineInputBorder()),
                    validator: (v) => v!.isEmpty ? 'Please enter description' : null,
                  ),
                  const SizedBox(height: 16),
                  Row(
                    children: [
                      const Text('Severity: '),
                      Expanded(
                        child: Slider(
                          value: _severity,
                          min: 1, max: 5, divisions: 4,
                          label: _getSeverityLabel(_severity),
                          onChanged: (v) => setState(() => _severity = v),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  TextFormField(
                    controller: _countController,
                    keyboardType: TextInputType.number,
                    decoration: const InputDecoration(labelText: 'Affected Count', border: OutlineInputBorder()),
                  ),
                ],
              ),
            ),
            Step(
              title: const Text('Review'),
              isActive: _currentStep >= 2,
              content: Card(
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      _buildReviewRow('Category', _category),
                      _buildReviewRow('District', _district),
                      _buildReviewRow('Severity', _getSeverityLabel(_severity)),
                      _buildReviewRow('Description', _descriptionController.text),
                      const SizedBox(height: 16),
                      const Text('Computed Urgency:', style: TextStyle(fontWeight: FontWeight.bold)),
                      const SizedBox(height: 8),
                      UrgencyBadge(score: (_severity * 20)),
                    ],
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  String _getSeverityLabel(double v) {
    switch (v.toInt()) {
      case 1: return 'Minor';
      case 2: return 'Low';
      case 3: return 'Moderate';
      case 4: return 'High';
      case 5: return 'Critical';
      default: return 'Unknown';
    }
  }

  Widget _buildReviewRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('$label: ', style: const TextStyle(fontWeight: FontWeight.bold)),
          Expanded(child: Text(value)),
        ],
      ),
    );
  }
}
