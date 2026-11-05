# Step 4: Lighter detection (Custom Vision object detection)

**Model:** project `lighter-detection`, tag `lighter`, 45 images, 60 boxes ([lighter_boxes.json](lighter_boxes.json)).
**Published iteration:** Iteration 3, Advanced training: precision 100%, recall 41.2%, mAP 92.4% (quick Iteration 2 was recall 17.6%, mAP 81.6%) (rubric needs precision ≥ 75%). Details: [lighter_model_metrics.json](lighter_model_metrics.json)

| Rubric item | Where |
|---|---|
| Screenshots: labeling on customvision.ai | **TODO (you):** customvision.ai → lighter-detection → Training Images → open an image (boxes visible) |
| Screenshots: training | **TODO (you):** the Train dialog or Iterations list on customvision.ai |
| Screenshots: validation | **TODO (you):** Performance tab (per-tag precision/recall, probability threshold slider) |
| Screenshot: precision and recall | **TODO (you):** Performance tab, published iteration |
| Code: model deployed to an endpoint, URL shared | [`scripts/lighter_detection.py`](../../../scripts/lighter_detection.py) `publish()`; endpoint in [lighter_model_metrics.json](lighter_model_metrics.json) |
| Code: prediction with the endpoint | [`kiosk/services/customvision.py`](../../../kiosk/services/customvision.py) `predict_lighter` (`detect_image`) · notebook "Step 4" |
| Lighter probability for each of the 5 test images | [lighter_predictions.json](lighter_predictions.json) · **TODO (you):** screenshot notebook "Step 4" or the Quick Test on customvision.ai |

| Test image | Lighter probability | At 0.5 |
|---|---|---|
| lighter_test_set_1of5.jpg | 52.1% | flagged |
| lighter_test_set_2of5.jpg | 78.1% | flagged |
| lighter_test_set_3of5.jpg | 29.5% | missed |
| lighter_test_set_4of5.jpg | 84.1% | flagged |
| lighter_test_set_5of5.jpg | 13.7% | missed |

All five trays contain a lighter. Images 3 and 5 still score below 0.5: their lighters are small and cluttered, unlike the studio training photos (domain shift; see the final reflection).
