import numpy as np


def dummy_predict_category(text):
    from complaints.models import ComplaintCategory

    cats = ComplaintCategory.objects.filter(is_active=True)
    if cats.exists():
        return cats.order_by("?").first()
    return None


def dummy_predict_anomaly(text, user_id, created_at):
    return np.random.choice([True, False], p=[0.1, 0.9])


def dummy_predict_sentiment(text):
    return np.random.choice(["positive", "negative", "neutral"])


# Örnek (dummy) YSA modeli: Gerçek bir model eğitimi veya yükleme işlemi yapılmadığından, dummy tahminler döndürüyorum.
# Gerçek uygulamada, burada TensorFlow, PyTorch veya scikit-learn ile eğitilmiş bir model yüklenir.

# Örnek: Complaint kaydedilirken (örneğin, bir sinyal veya view içinde) aşağıdaki gibi çağrılabilir:
# (Not: Gerçek bir model kullanılmadığından, dummy tahminler döndürüyoruz.)

# def auto_process_complaint(complaint):
#     text = complaint.description
#     user_id = complaint.created_by.id
#     created_at = complaint.created_at
#     # Otomatik sınıflandırma (ör. kategori tahmini)
#     pred_cat = dummy_predict_category(text)
#     if pred_cat:
#         complaint.category = pred_cat
#     # Anomali tespiti (ör. dolandırıcılık tespiti)
#     is_anomaly = dummy_predict_anomaly(text, user_id, created_at)
#     if is_anomaly:
#         # Anomali tespit edildiğinde, örneğin bir bayrak (flag) veya özel bir durum (status) atanabilir.
#         # Örnek: complaint.is_anomaly = True
#         pass
#     # Duygu analizi (sentiment)
#     sentiment = dummy_predict_sentiment(text)
#     # Örnek: complaint.sentiment = sentiment
#     complaint.save()

# (Not: Gerçek uygulamada, burada modelin tahminleri kullanılır ve Complaint modeline eklenir.)
