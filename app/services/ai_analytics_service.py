# ====================================================================
# AI ANALYTICS SERVICE - GROQ INTEGRATION
# ====================================================================
# Service ini menghubungkan sistem dengan Groq API (Llama 3.3 70B) untuk
# mendapatkan insight dan analisis cerdas dari data billing.
# Groq menyediakan akses gratis ke model Llama 3.3 70B yang sangat cepat.
# ====================================================================

from __future__ import annotations
import asyncio
import json
import logging
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

import httpx

from ..config import settings

logger = logging.getLogger("app.analytics")


# ====================================================================
# Groq API CLIENT
# ====================================================================

class GroqClient:
    """
    Client untuk berkomunikasi dengan Groq API.
    Menggunakan Llama 3.3 70B Versatile model (Gratis & Sangat Cepat).
    OpenAI-compatible API.
    """

    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        self.base_url = settings.GROQ_BASE_URL
        self.model = settings.GROQ_MODEL  # llama-3.3-70b-versatile
        self.timeout = 30.0  # 30 seconds timeout

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 2000
    ) -> str:
        """
        Mengirim request ke Groq Chat Completions API (OpenAI-compatible).
        Dengan retry logic untuk handling rate limit (429).

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: 0.0-1.0, lower = more focused
            max_tokens: Maximum tokens in response

        Returns:
            str: AI response text

        Raises:
            httpx.HTTPError: If API request fails after all retries
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False
        }

        # Retry configuration untuk handling rate limit
        max_retries = 5
        base_delay = 1.0  # seconds

        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        f"{self.base_url}/chat/completions",
                        headers=headers,
                        json=payload
                    )

                    # Handle rate limiting (429)
                    if response.status_code == 429:
                        retry_after = response.headers.get("Retry-After")

                        # Parse error message untuk suggested wait time
                        try:
                            error_data = response.json()
                            error_msg = error_data.get("error", {}).get("message", "")
                            # Extract "Please try again in X.XXs"
                            import re
                            match = re.search(r"try again in (\d+\.?\d*)s", error_msg)
                            if match:
                                suggested_delay = float(match.group(1))
                                delay = suggested_delay
                            else:
                                delay = base_delay * (2 ** attempt)  # Exponential backoff
                        except:
                            delay = base_delay * (2 ** attempt)

                        # Use retry_after header if available
                        if retry_after:
                            delay = float(retry_after)

                        if attempt < max_retries - 1:
                            logger.warning(
                                f"Rate limit hit (429). Retry {attempt + 1}/{max_retries} "
                                f"after {delay:.2f}s"
                            )
                            await asyncio.sleep(delay)
                            continue
                        else:
                            logger.error(f"Max retries reached for rate limit")
                            response.raise_for_status()

                    response.raise_for_status()

                    result = response.json()

                    # Log the full API response for debugging
                    logger.info(f"Groq API response status: {response.status_code}")
                    logger.info(f"Groq API response keys: {list(result.keys()) if isinstance(result, dict) else type(result)}")

                    # Extract the AI response
                    if "choices" in result and len(result["choices"]) > 0:
                        content = result["choices"][0]["message"]["content"]
                        logger.info(f"Content length: {len(content) if content else 0} chars")
                        logger.info(f"Content preview (first 200 chars): {content[:200] if content else 'EMPTY'}")

                        if content:
                            return content
                        else:
                            logger.error(f"Empty content in API response. Full result: {result}")
                            raise ValueError("Empty content returned from Groq API")
                    else:
                        logger.error(f"Unexpected API response format. Full result: {result}")
                        raise ValueError("Unexpected API response format from Groq")

            except httpx.HTTPStatusError as e:
                # Jika bukan 429, langsung raise
                if e.response.status_code != 429:
                    logger.error(f"Groq API HTTP error: {e.response.status_code} - {e.response.text}")
                    raise
                # Jika 429 dan sudah max retries, raise
                if attempt == max_retries - 1:
                    logger.error(f"Groq API HTTP error after retries: {e.response.status_code} - {e.response.text}")
                    raise

            except httpx.TimeoutException:
                logger.error("Groq API timeout")
                raise

            except Exception as e:
                logger.error(f"Unexpected error calling Groq: {e}")
                raise

        # Should not reach here, but just in case
        raise Exception("Max retries exceeded")

    async def analyze_data(
        self,
        system_prompt: str,
        user_prompt: str,
        data: Dict[str, Any]
    ) -> str:
        """
        Analisis data dengan Groq.

        Args:
            system_prompt: System message defining AI role
            user_prompt: User request/question
            data: Data to analyze (will be JSON serialized)

        Returns:
            str: AI analysis result
        """
        messages = [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": f"{user_prompt}\n\nData:\n{json.dumps(data, ensure_ascii=False, indent=2)}"
            }
        ]

        return await self.chat_completion(messages)


# ====================================================================
# AI ANALYTICS SERVICE
# ====================================================================

class AIAnalyticsService:
    """
    Service utama untuk AI Analytics.
    Menggunakan Groq untuk menganalisis data billing dan memberikan insight.
    """

    def __init__(self):
        self.groq_client = GroqClient()

    # --------------------------------------------------------------------
    # REVENUE ANALYSIS
    # --------------------------------------------------------------------

    async def analyze_revenue(
        self,
        revenue_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Menganalisis data pendapatan dan memberikan insight.

        Args:
            revenue_data: Data pendapatan dari DataAggregationService

        Returns:
            Dict berisi:
            - summary: Ringkasan analisis
            - key_findings: List temuan penting
            - recommendations: List rekomendasi
            - opportunities: List peluang bisnis
        """
        system_prompt = """Anda adalah analisis keuangan expert untuk ISP (Internet Service Provider).
Tugas Anda adalah menganalisis data pendapatan dan memberikan insight yang actionable.

Bahasa output: Bahasa Indonesia yang formal namun mudah dipahami.

Format output dalam JSON (HANYA output JSON, tanpa markdown atau teks tambahan):
{
  "summary": "Ringkasan analisis pendapatan dalam 2-3 kalimat",
  "key_findings": [
    "Temuan 1",
    "Temuan 2"
  ],
  "recommendations": [
    "Rekomendasi 1",
    "Rekomendasi 2"
  ],
  "opportunities": [
    "Peluang 1",
    "Peluang 2"
  ],
  "risks": [
    "Risiko 1",
    "Risiko 2"
  ]
}

PENTING: Output HANYA valid JSON, tanpa ```json atau ``` di awal/akhir."""

        user_prompt = """Analisis data pendapatan ISP berikut dan berikan insight tentang:
1. Tren pendapatan (apakah meningkat/menurun?)
2. Collection rate (persentase pembayaran berhasil)
3. Pertumbuhan per brand
4. Prediksi pendapatan bulan depan
5. Metode pembayaran paling populer
6. Peluang peningkatan pendapatan
7. Risiko yang perlu diwaspadai

Jawab dalam format JSON yang valid. HANYA output JSON."""

        try:
            response = await self.groq_client.analyze_data(
                system_prompt,
                user_prompt,
                revenue_data
            )

            # Log the raw response for debugging
            logger.info(f"Raw AI response length: {len(response)} chars")
            logger.info(f"Raw AI response (first 500 chars): {response[:500]}")

            # Clean response - remove markdown code blocks if present
            cleaned_response = response.strip()

            # Remove markdown code blocks
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.startswith("```"):
                cleaned_response = cleaned_response[3:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()

            # Validate cleaned response is not empty
            if not cleaned_response:
                logger.error("Empty response after cleaning")
                raise ValueError("Response is empty after cleaning")

            # Check if it looks like JSON
            if not cleaned_response.startswith("{") and not cleaned_response.startswith("["):
                logger.error(f"Response doesn't look like JSON. First char: '{cleaned_response[0]}'")
                raise ValueError("Response is not JSON format")

            logger.info(f"Cleaned response (first 200 chars): {cleaned_response[:200]}")

            result = json.loads(cleaned_response)

            # Add metadata
            result["data_snapshot"] = {
                "total_revenue": revenue_data.get("total_revenue", 0),
                "paid_revenue": revenue_data.get("paid_revenue", 0),
                "collection_rate": revenue_data.get("collection_rate", 0),
                "growth_rate": revenue_data.get("growth_rate", 0),
                "forecast_next_month": revenue_data.get("forecast_next_month", 0)
            }

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            logger.error(f"Response that failed to parse: {response[:1000]}")
            # Fallback: wrap the text response
            return {
                "summary": f"Gagal memproses analisis AI. Error: {str(e)}",
                "key_findings": [
                    "Analisis AI mengalami kesalahan format JSON.",
                    f"Technical detail: {str(e)}"
                ],
                "recommendations": ["Coba lagi beberapa saat lagi"],
                "opportunities": [],
                "risks": [],
                "data_snapshot": {
                    "total_revenue": revenue_data.get("total_revenue", 0),
                    "paid_revenue": revenue_data.get("paid_revenue", 0)
                }
            }

        except Exception as e:
            logger.error(f"Unexpected error in analyze_revenue: {e}")
            return {
                "summary": f"Terjadi kesalahan: {str(e)}",
                "key_findings": [f"Error: {str(e)}"],
                "recommendations": [],
                "opportunities": [],
                "risks": [],
                "data_snapshot": {
                    "total_revenue": revenue_data.get("total_revenue", 0),
                    "paid_revenue": revenue_data.get("paid_revenue", 0)
                }
            }

    # --------------------------------------------------------------------
    # LATE PAYMENT ANALYSIS
    # --------------------------------------------------------------------

    async def analyze_late_payments(
        self,
        late_payment_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Menganalisis data pembayaran telat dan memberikan insight.

        Args:
            late_payment_data: Data pembayaran telat dari DataAggregationService

        Returns:
            Dict berisi:
            - summary: Ringkasan analisis
            - risk_assessment: Evaluasi risiko
            - follow_up_strategy: Strategi follow-up
            - prevention_recommendations: Rekomendasi pencegahan
        """
        system_prompt = """Anda adalah expert dalam manajemen piutang dan collections untuk ISP.
Tugas Anda adalah menganalisis data pembayaran telat dan memberikan strategi penagihan yang efektif.

Bahasa output: Bahasa Indonesia yang formal namun mudah dipahami.

Format output dalam JSON (HANYA output JSON, tanpa markdown atau teks tambahan):
{
  "summary": "Ringkasan situasi pembayaran telat",
  "risk_assessment": {
    "overall_risk": "HIGH/MEDIUM/LOW",
    "total_outstanding": "Estimasi total outstanding",
    "critical_customers": "Jumlah customer critical"
  },
  "follow_up_strategy": [
    "Strategi 1",
    "Strategi 2"
  ],
  "prevention_recommendations": [
    "Rekomendasi 1",
    "Rekomendasi 2"
  ],
  "communication_template": {
    "high_priority": "Template pesan untuk high priority",
    "medium_priority": "Template pesan untuk medium priority",
    "low_priority": "Template pesan untuk low priority"
  }
}

PENTING: Output HANYA valid JSON, tanpa ```json atau ``` di awal/akhir."""

        user_prompt = """Analisis data pembayaran telat berikut dan berikan:
1. Penilaian tingkat risiko secara keseluruhan
2. Segmentasi customer berdasarkan risiko
3. Strategi follow-up yang efektif untuk setiap segment
4. Template pesan WhatsApp/Email untuk follow-up
5. Rekomendasi untuk mencegah pembayaran telat di masa depan

Catatan: Data nama, email, dan telepon sudah di-mask untuk privacy.

Jawab dalam format JSON yang valid. HANYA output JSON."""

        try:
            response = await self.groq_client.analyze_data(
                system_prompt,
                user_prompt,
                late_payment_data
            )

            logger.info(f"Raw AI response length: {len(response)} chars")
            logger.info(f"Raw AI response (first 500 chars): {response[:500]}")

            # Clean response - remove markdown code blocks if present
            cleaned_response = response.strip()

            # Remove markdown code blocks
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.startswith("```"):
                cleaned_response = cleaned_response[3:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()

            # Validate cleaned response is not empty
            if not cleaned_response:
                logger.error("Empty response after cleaning")
                raise ValueError("Response is empty after cleaning")

            # Check if it looks like JSON
            if not cleaned_response.startswith("{") and not cleaned_response.startswith("["):
                logger.error(f"Response doesn't look like JSON. First char: '{cleaned_response[0]}'")
                raise ValueError("Response is not JSON format")

            logger.info(f"Cleaned response (first 200 chars): {cleaned_response[:200]}")

            result = json.loads(cleaned_response)

            # Add metadata
            result["data_snapshot"] = {
                "total_late_customers": late_payment_data.get("total_late_customers", 0),
                "total_outstanding": late_payment_data.get("total_outstanding", 0),
                "avg_days_late": late_payment_data.get("avg_days_late", 0)
            }

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            logger.error(f"Response that failed to parse: {response[:1000]}")
            return {
                "summary": f"Gagal memproses analisis AI. Error: {str(e)}",
                "risk_assessment": {
                    "overall_risk": "UNKNOWN",
                    "total_outstanding": "N/A",
                    "critical_customers": "N/A"
                },
                "follow_up_strategy": [],
                "prevention_recommendations": [],
                "communication_template": {},
                "data_snapshot": {
                    "total_late_customers": late_payment_data.get("total_late_customers", 0),
                    "total_outstanding": late_payment_data.get("total_outstanding", 0)
                }
            }

        except Exception as e:
            logger.error(f"Unexpected error in analyze_late_payments: {e}")
            return {
                "summary": f"Terjadi kesalahan: {str(e)}",
                "risk_assessment": {
                    "overall_risk": "UNKNOWN",
                    "total_outstanding": "N/A",
                    "critical_customers": "N/A"
                },
                "follow_up_strategy": [],
                "prevention_recommendations": [],
                "communication_template": {},
                "data_snapshot": {
                    "total_late_customers": late_payment_data.get("total_late_customers", 0),
                    "total_outstanding": late_payment_data.get("total_outstanding", 0)
                }
            }

    # --------------------------------------------------------------------
    # CUSTOMER BEHAVIOR ANALYSIS
    # --------------------------------------------------------------------

    async def analyze_customer_behavior(
        self,
        customer_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Menganalisis behavior customer dan memberikan insight.

        Args:
            customer_data: Data customer dari DataAggregationService

        Returns:
            Dict berisi:
            - summary: Ringkasan analisis
            - customer_insights: Insight tentang customer
            - retention_strategies: Strategi retensi
            - growth_opportunities: Peluang pertumbuhan
        """
        system_prompt = """Anda adalah expert dalam customer relationship management (CRM) untuk ISP.
Tugas Anda adalah menganalisis perilaku customer dan memberikan strategi retensi serta upselling.

Bahasa output: Bahasa Indonesia yang formal namun mudah dipahami.

Format output dalam JSON (HANYA output JSON, tanpa markdown atau teks tambahan):
{
  "summary": "Ringkasan analisis perilaku customer",
  "customer_insights": {
    "total_customers": "Total customer dianalisis",
    "avg_clv": "Rata-rata Customer Lifetime Value",
    "churn_risk_level": "Tingkat risiko churn"
  },
  "segment_analysis": [
    {
      "segment": "Nama segment",
      "characteristics": "Ciri-ciri segment",
      "strategy": "Strategi untuk segment ini"
    }
  ],
  "retention_strategies": [
    "Strategi 1",
    "Strategi 2"
  ],
  "upsell_opportunities": [
    "Peluang 1",
    "Peluang 2"
  ]
}

PENTING: Output HANYA valid JSON, tanpa ```json atau ``` di awal/akhir."""

        user_prompt = """Analisis data perilaku customer berikut dan berikan:
1. Analisis segmentasi customer yang ada
2. Customer Lifetime Value (CLV) analysis
3. Tingkat risiko churn dan customer yang berisiko
4. Strategi retensi untuk setiap segment
5. Peluang upselling/cross-selling
6. Saran program loyalty yang efektif

Catatan: Data nama dan kontak customer sudah di-mask untuk privacy.

Jawab dalam format JSON yang valid. HANYA output JSON."""

        try:
            response = await self.groq_client.analyze_data(
                system_prompt,
                user_prompt,
                customer_data
            )

            logger.info(f"Raw AI response length: {len(response)} chars")
            logger.info(f"Raw AI response (first 500 chars): {response[:500]}")

            # Clean response - remove markdown code blocks if present
            cleaned_response = response.strip()

            # Remove markdown code blocks
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.startswith("```"):
                cleaned_response = cleaned_response[3:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()

            # Validate cleaned response is not empty
            if not cleaned_response:
                logger.error("Empty response after cleaning")
                raise ValueError("Response is empty after cleaning")

            # Check if it looks like JSON
            if not cleaned_response.startswith("{") and not cleaned_response.startswith("["):
                logger.error(f"Response doesn't look like JSON. First char: '{cleaned_response[0]}'")
                raise ValueError("Response is not JSON format")

            logger.info(f"Cleaned response (first 200 chars): {cleaned_response[:200]}")

            result = json.loads(cleaned_response)

            # Add metadata
            result["data_snapshot"] = {
                "total_customers": customer_data.get("total_customers_analyzed", 0),
                "avg_loyalty_score": customer_data.get("loyalty_analysis", {}).get("avg_loyalty_score", 0),
                "avg_churn_risk": customer_data.get("churn_risk_analysis", {}).get("avg_churn_risk", 0)
            }

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            logger.error(f"Response that failed to parse: {response[:1000]}")
            return {
                "summary": f"Gagal memproses analisis AI. Error: {str(e)}",
                "customer_insights": {
                    "total_customers": "N/A",
                    "avg_clv": "N/A",
                    "churn_risk_level": "UNKNOWN"
                },
                "segment_analysis": [],
                "retention_strategies": [],
                "upsell_opportunities": [],
                "data_snapshot": {
                    "total_customers": customer_data.get("total_customers_analyzed", 0),
                    "avg_loyalty_score": 0,
                    "avg_churn_risk": 0
                }
            }

        except Exception as e:
            logger.error(f"Unexpected error in analyze_customer_behavior: {e}")
            return {
                "summary": f"Terjadi kesalahan: {str(e)}",
                "customer_insights": {
                    "total_customers": "N/A",
                    "avg_clv": "N/A",
                    "churn_risk_level": "UNKNOWN"
                },
                "segment_analysis": [],
                "retention_strategies": [],
                "upsell_opportunities": [],
                "data_snapshot": {
                    "total_customers": customer_data.get("total_customers_analyzed", 0),
                    "avg_loyalty_score": 0,
                    "avg_churn_risk": 0
                }
            }

    # --------------------------------------------------------------------
    # CHAT INTERACTION
    # --------------------------------------------------------------------

    async def chat_analytics(
        self,
        question: str,
        context_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Chat interface untuk pertanyaan analytics secara natural language.

        Args:
            question: Pertanyaan dari user
            context_data: Data konteks (opsional)

        Returns:
            str: Jawaban dari AI
        """
        system_prompt = """Anda adalah asisten analytics untuk sistem billing ISP.
Tugas Anda adalah menjawab pertanyaan tentang data pendapatan, pembayaran, dan perilaku customer.

Bahasa output: Bahasa Indonesia yang ramah dan profesional.

FORMAT OUTPUT - WAJIB:
Gunakan format Markdown untuk jawaban yang mudah dibaca:
- Gunakan **bold** untuk highlight penting
- Gunakan bullet points untuk daftar
- Gunakan tabel untuk data customer
- Gunakan emoji untuk visual (opsional)
- Pisahkan bagian dengan heading/judul

Contoh format tabel:
| Nama Customer | Churn Risk | Segment | Total Belanja |
|---------------|------------|---------|---------------|
| Budi Santoso  | 100%       | At Risk | Rp 1.500.000  |

Contoh format list:
**Customer dengan risiko tertinggi:**
1. **Nama Customer** - Risk: 90%
   - Alasan: Pembayaran sering telat
   - Tindakan: Hubungi segera

STRUKTUR DATA YANG MUNGKIN DITERIMA:

1. REVENUE DATA (Pendapatan):
   - total_revenue: Total pendapatan
   - paid_revenue: Pendapatan yang sudah dibayar
   - collection_rate: Persentase pembayaran berhasil
   - growth_rate: Tingkat pertumbuhan
   - total_invoices: Total jumlah invoice

2. CUSTOMER BEHAVIOR DATA:
   - total_customers: JUMLAH TOTAL SEMUA PELANGGAN (ini yang paling penting!)
   - total_customers_analyzed: Jumlah customer yang dianalisis (punya invoice)
   - customers_with_recent_activity: Customer dengan aktivitas 6 bulan terakhir
   - customer_segments: Segmentasi customer
   - churn_risk_analysis: Analisis risiko churn
   - high_risk_customers: List customer dengan churn_risk tinggi

3. LATE PAYMENT DATA:
   - total_late_customers: Jumlah customer telat bayar
   - total_outstanding: Total uang tertunda
   - avg_days_late: Rata-rata hari keterlambatan

Jawab pertanyaan dengan jelas, gunakan tabel untuk data customer, dan berikan insight yang actionable.
Jika user bertanya tentang jumlah pelanggan, gunakan field "total_customers" dari customer behavior data.
Untuk pertanyaan tentang customer berisiko, tampilkan dalam tabel dengan nama lengkap, skor, dan rekomendasi."""

        user_message = question
        if context_data:
            user_message += f"\n\nData konteks:\n{json.dumps(context_data, ensure_ascii=False, indent=2)}"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]

        return await self.groq_client.chat_completion(messages)
