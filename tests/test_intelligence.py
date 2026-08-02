import unittest
from event_detector import EventDetector
from document_classifier import DocumentClassifier
from section_detector import SectionDetector

class TestIntelligenceLayer(unittest.TestCase):
    def setUp(self):
        self.doc_classifier = DocumentClassifier()
        self.event_detector = EventDetector()
        self.section_detector = SectionDetector()
        
    def test_benchmark_framework(self):
        """
        Final Objective: Permanent Benchmark Suite
        Automatically runs regressions against correctly labelled historical announcements.
        """
        # Detailed Dictionary Format for strict regression testing
        dataset = [
            {
                "blocks": ["PROPOSAL FOR MERGER OF ABC LTD", "The Board of Directors will consider the draft scheme of amalgamation at the next meeting."],
                "expected_doc": "Unknown Document",
                "expected_event": "Needs Manual Review",
                "expected_rejected_count": 1 # Should reject merger due to "proposal" and missing action
            },
            {
                "blocks": ["Outcome of Board Meeting", "The Board has recommended a final dividend of Rs 5 per share."],
                "expected_doc": "Dividend",
                "expected_event": "Dividend",
                "expected_rejected_count": 0
            },
            {
                "blocks": ["Letter of Award for Railway Project", "We are pleased to inform you that the company has secured a Letter of Award from Ministry of Railways for Rs 500 Cr."],
                "expected_doc": "Government Contract",
                "expected_event": "Government Contract",
                "expected_rejected_count": 0
            },
            {
                "blocks": ["Notice of AGM", "The Annual General Meeting will be held to vote on the Government Contract."],
                "expected_doc": "AGM Notice",
                "expected_event": "Needs Manual Review", # AGM notices drop confidence heavily
                "expected_rejected_count": 1 # Government contract blocked by classifier
            }
        ]
        
        confusion_matrix = {"True Positive": 0, "False Positive": 0, "False Negative": 0}
        
        for data in dataset:
            blocks = data["blocks"]
            expected = data["expected_event"]
            text = "\n".join(blocks)
            doc_type, conf, allowed = self.doc_classifier.classify_document(blocks[0], text)
            
            # 1. Check Document Classification
            if data.get("expected_doc") != "Unknown Document":
                self.assertEqual(doc_type, data["expected_doc"])
            
            # Using Section Detector
            weighted = self.section_detector.get_weighted_blocks(blocks)
            events, rejected = self.event_detector.detect_events(weighted, allowed)
            
            # Check Explainability tracing
            self.assertGreaterEqual(len(rejected), data.get("expected_rejected_count", 0))
            
            # Fallback simple selection for testing
            best_event = None
            if events:
                best_event = max(events, key=lambda x: x.confidence)
                
            predicted = best_event.category if best_event else "Needs Manual Review"
            if doc_type == "Unknown Document": predicted = "Needs Manual Review"
            
            if predicted == "Needs Manual Review" and expected == "Needs Manual Review":
                confusion_matrix["True Positive"] += 1
            elif expected == predicted:
                confusion_matrix["True Positive"] += 1
            elif predicted != "Needs Manual Review" and expected != predicted:
                confusion_matrix["False Positive"] += 1
            elif predicted == "Needs Manual Review" and expected != "Needs Manual Review":
                confusion_matrix["False Negative"] += 1
                
        accuracy = confusion_matrix["True Positive"] / len(dataset)
        print(f"\n--- Final Optimisation Benchmark Results ---")
        print(f"Accuracy: {accuracy*100:.2f}%")
        print(f"Confusion Matrix: {confusion_matrix}")
        
        # Enforce Regression Protection (Requirement 12)
        self.assertGreaterEqual(accuracy, 1.0) # Cannot merge if it degrades below 100% on the core set
        self.assertEqual(confusion_matrix["False Positive"], 0) # Must never regress on False Positives

if __name__ == '__main__':
    unittest.main()
