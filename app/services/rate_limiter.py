"""
Rate Limiter Service for Xendit API.
Non-intrusive wrapper untuk mencegah rate limiting dan memastikan semua invoice terkirim.

Features:
- Rate limiting untuk Xendit API
- Automatic retry dengan exponential backoff
- Queue system untuk bulk operations
- Error recovery dan logging
- Non-intrusive integration dengan existing code

Usage:
1. Import rate_limiter di file yang memanggil create_xendit_invoice
2. Ganti direct call dengan rate_limiter.create_invoice_with_rate_limit()
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

from ..services.xendit_service import create_xendit_invoice
from ..models.invoice import Invoice as InvoiceModel
from ..models.pelanggan import Pelanggan as PelangganModel
from ..models.paket_layanan import PaketLayanan as PaketLayananModel

logger = logging.getLogger("app.services.rate_limiter")


class InvoicePriority(Enum):
    """Priority levels untuk invoice creation."""
    HIGH = "high"      # VIP customers, urgent invoices
    NORMAL = "normal"  # Regular customers
    LOW = "low"        # Bulk operations, non-urgent


@dataclass
class InvoiceRequest:
    """Data structure untuk invoice request."""
    invoice: InvoiceModel
    pelanggan: PelangganModel
    paket: PaketLayananModel
    deskripsi_xendit: str
    pajak: float
    no_telp_xendit: str = ""
    priority: InvoicePriority = InvoicePriority.NORMAL
    retry_count: int = 0
    created_at: Optional[datetime] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class RateLimiterService:
    """
    Rate limiter service untuk Xendit API calls.

    Configurations:
    - max_requests_per_second: Max requests ke Xendit API
    - max_retries: Maximum retry attempts
    - base_delay: Base delay untuk retry (seconds)
    - max_delay: Maximum delay untuk retry (seconds)
    """

    def __init__(self):
        self.max_requests_per_second = 1  # CONSERVATIVE untuk stability
        self.max_retries = 5              # MORE retry attempts
        self.base_delay = 2.0             # LONGER delay untuk safety
        self.max_delay = 60.0             # MAX delay untuk recovery

        # Rate limiting state
        self.last_request_time = 0.0
        self.request_count = 0
        self.window_start = time.time()

        # Queue untuk pending requests
        self.pending_queue: List[InvoiceRequest] = []
        self.processing_queue: List[InvoiceRequest] = []
        self.completed_queue: List[InvoiceRequest] = []
        self.failed_queue: List[InvoiceRequest] = []

        # Processing state
        self.is_processing = False
        self.total_processed = 0
        self.total_failed = 0

    async def create_invoice_with_rate_limit(
        self,
        invoice: InvoiceModel,
        pelanggan: PelangganModel,
        paket: PaketLayananModel,
        deskripsi_xendit: str,
        pajak: float,
        no_telp_xendit: str = "",
        priority: InvoicePriority = InvoicePriority.NORMAL
    ) -> Dict[str, Any]:
        """
        Create invoice dengan rate limiting dan retry logic.

        Ini adalah wrapper function yang menggantikan direct call ke create_xendit_invoice.
        Tidak mengubah logika bisnis, hanya menambah rate limiting dan retry.

        Args:
            Sama seperti create_xendit_invoice original

        Returns:
            Dict dengan Xendit response atau error information
        """

        request = InvoiceRequest(
            invoice=invoice,
            pelanggan=pelanggan,
            paket=paket,
            deskripsi_xendit=deskripsi_xendit,
            pajak=pajak,
            no_telp_xendit=no_telp_xendit,
            priority=priority
        )

        # Jika ini bulk operation, tambahkan ke queue
        if len(self.pending_queue) > 0 or len(self.processing_queue) > 0:
            return await self._add_to_queue(request)

        # Jika single request, proses langsung dengan rate limiting
        return await self._process_single_request(request)

    async def create_bulk_invoices_with_rate_limit(
        self,
        invoices_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Create multiple invoices dengan rate limiting dan queue system.

        Args:
            invoices_data: List of dictionaries dengan invoice data

        Returns:
            Dict dengan summary hasil bulk creation
        """

        logger.info(f"📦 Starting bulk invoice creation: {len(invoices_data)} invoices")

        # Create InvoiceRequest objects
        requests = []
        for data in invoices_data:
            request = InvoiceRequest(
                invoice=data['invoice'],
                pelanggan=data['pelanggan'],
                paket=data['paket'],
                deskripsi_xendit=data['deskripsi_xendit'],
                pajak=data['pajak'],
                no_telp_xendit=data.get('no_telp_xendit', ''),
                priority=data.get('priority', InvoicePriority.NORMAL)
            )
            requests.append(request)

        # Sort by priority
        priority_order = {
            InvoicePriority.HIGH: 0,
            InvoicePriority.NORMAL: 1,
            InvoicePriority.LOW: 2
        }
        requests.sort(key=lambda x: priority_order[x.priority])

        # Add to queue
        self.pending_queue.extend(requests)

        # Start processing if not already running
        if not self.is_processing:
            asyncio.create_task(self._process_queue())

        return {
            "success": True,
            "message": f"Added {len(requests)} invoices to processing queue",
            "queue_status": await self.get_queue_status()
        }

    async def _add_to_queue(self, request: InvoiceRequest) -> Dict[str, Any]:
        """Add request to queue and return immediate response."""
        self.pending_queue.append(request)

        # Start processing if not already running
        if not self.is_processing:
            asyncio.create_task(self._process_queue())

        return {
            "success": True,
            "message": f"Invoice {request.invoice.invoice_number} added to queue",
            "queue_position": len(self.pending_queue),
            "estimated_wait_time": self._estimate_wait_time()
        }

    async def _process_single_request(self, request: InvoiceRequest) -> Dict[str, Any]:
        """Process single request dengan rate limiting."""

        # Apply rate limiting delay
        await self._apply_rate_limit_delay()

        # Process dengan retry logic
        return await self._process_with_retry(request)

    async def _process_queue(self) -> None:
        """Process all pending requests in queue."""

        if self.is_processing:
            return

        self.is_processing = True
        logger.info("🚀 Starting queue processing...")

        try:
            while self.pending_queue or self.processing_queue:
                # Process pending requests
                if self.pending_queue:
                    # Move batch from pending to processing
                    batch_size = min(5, len(self.pending_queue))  # Process 5 at a time
                    batch = self.pending_queue[:batch_size]
                    self.pending_queue = self.pending_queue[batch_size:]
                    self.processing_queue.extend(batch)

                    logger.info(f"📋 Processing batch: {len(batch)} invoices")

                # Process current batch
                if self.processing_queue:
                    await self._process_batch(self.processing_queue.copy())

                # Small delay between batches
                await asyncio.sleep(1)

        finally:
            self.is_processing = False
            logger.info("✅ Queue processing completed")

            # Log final statistics
            await self._log_final_statistics()

    async def _process_batch(self, batch: List[InvoiceRequest]) -> None:
        """Process a batch of requests concurrently."""

        tasks = []
        for request in batch:
            task = asyncio.create_task(self._process_with_retry(request))
            tasks.append(task)

        # Wait for all tasks in batch to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle results
        for i, result in enumerate(results):
            request = batch[i]
            self.processing_queue.remove(request)

            if isinstance(result, Exception):
                logger.error(f"❌ Invoice {request.invoice.invoice_number} failed: {result}")
                self.failed_queue.append(request)
                self.total_failed += 1
            else:
                logger.info(f"✅ Invoice {request.invoice.invoice_number} processed successfully")
                self.completed_queue.append(request)
                self.total_processed += 1

    async def _process_with_retry(self, request: InvoiceRequest) -> Dict[str, Any]:
        """Process request dengan exponential backoff retry."""

        for attempt in range(self.max_retries + 1):
            try:
                # Apply rate limiting delay
                await self._apply_rate_limit_delay()

                # Call original function
                result = await create_xendit_invoice(
                    invoice=request.invoice,
                    pelanggan=request.pelanggan,
                    paket=request.paket,
                    deskripsi_xendit=request.deskripsi_xendit,
                    pajak=request.pajak,
                    no_telp_xendit=request.no_telp_xendit
                )

                logger.info(f"✅ Invoice {request.invoice.invoice_number} created successfully (attempt {attempt + 1})")
                return result

            except Exception as e:
                request.retry_count = attempt

                if attempt < self.max_retries:
                    # Calculate delay dengan exponential backoff
                    delay = min(self.base_delay * (2 ** attempt), self.max_delay)

                    logger.warning(
                        f"⚠️ Invoice {request.invoice.invoice_number} failed (attempt {attempt + 1}), "
                        f"retrying in {delay:.1f}s. Error: {str(e)}"
                    )

                    await asyncio.sleep(delay)
                else:
                    # Final attempt failed
                    logger.error(
                        f"❌ Invoice {request.invoice.invoice_number} failed after {self.max_retries + 1} attempts. "
                        f"Final error: {str(e)}"
                    )
                    # Return error result instead of raising
                    return {
                        "success": False,
                        "error": str(e),
                        "invoice_number": request.invoice.invoice_number,
                        "attempts": self.max_retries + 1
                    }

        # This should never be reached, but satisfies type checker
        return {
            "success": False,
            "error": "Unexpected error in retry logic",
            "invoice_number": request.invoice.invoice_number,
            "attempts": self.max_retries + 1
        }

    async def _apply_rate_limit_delay(self) -> None:
        """Apply delay untuk rate limiting."""

        current_time = time.time()

        # Reset window jika sudah lewat
        if current_time - self.window_start >= 1.0:
            self.request_count = 0
            self.window_start = current_time

        # Check rate limit
        if self.request_count >= self.max_requests_per_second:
            # Calculate time until next window
            time_until_next_window = 1.0 - (current_time - self.window_start)

            if time_until_next_window > 0:
                logger.info(f"⏳ Rate limiting: waiting {time_until_next_window:.1f}s")
                await asyncio.sleep(time_until_next_window)

                # Reset window
                self.request_count = 0
                self.window_start = time.time()

        # Update request tracking
        self.request_count += 1
        self.last_request_time = current_time

    def _estimate_wait_time(self) -> float:
        """Estimate wait time untuk queue."""

        total_requests = len(self.pending_queue) + len(self.processing_queue)
        estimated_time = total_requests / self.max_requests_per_second

        return min(estimated_time, 300)  # Max 5 minutes estimate

    async def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status."""

        return {
            "pending": len(self.pending_queue),
            "processing": len(self.processing_queue),
            "completed": len(self.completed_queue),
            "failed": len(self.failed_queue),
            "total_processed": self.total_processed,
            "total_failed": self.total_failed,
            "is_processing": self.is_processing,
            "estimated_wait_time": self._estimate_wait_time()
        }

    async def retry_failed_invoices(self) -> Dict[str, Any]:
        """Retry all failed invoices."""

        if not self.failed_queue:
            return {"success": True, "message": "No failed invoices to retry"}

        failed_count = len(self.failed_queue)
        failed_invoices = self.failed_queue.copy()
        self.failed_queue.clear()

        # Reset retry count and add back to pending queue
        for invoice in failed_invoices:
            invoice.retry_count = 0
            self.pending_queue.append(invoice)

        # Start processing if not already running
        if not self.is_processing:
            asyncio.create_task(self._process_queue())

        return {
            "success": True,
            "message": f"Retrying {failed_count} failed invoices",
            "queue_status": await self.get_queue_status()
        }

    async def _log_final_statistics(self) -> None:
        """Log final statistics after queue processing."""

        total = self.total_processed + self.total_failed
        if total > 0:
            success_rate = (self.total_processed / total) * 100

            logger.info(f"📊 Queue Processing Statistics:")
            logger.info(f"   Total processed: {total}")
            logger.info(f"   Successful: {self.total_processed} ({success_rate:.1f}%)")
            logger.info(f"   Failed: {self.total_failed}")

            if self.total_failed > 0:
                logger.warning(f"⚠️ {self.total_failed} invoices failed. Consider retrying.")


# Global instance untuk easy access
rate_limiter = RateLimiterService()


# Convenience functions untuk easy integration
async def create_invoice_with_rate_limit(
    invoice: InvoiceModel,
    pelanggan: PelangganModel,
    paket: PaketLayananModel,
    deskripsi_xendit: str,
    pajak: float,
    no_telp_xendit: str = "",
    priority: InvoicePriority = InvoicePriority.NORMAL
) -> Dict[str, Any]:
    """
    Convenience function untuk single invoice creation dengan rate limiting.

    Ganti direct call ke create_xendit_invoice dengan function ini:

    # Original:
    # result = await create_xendit_invoice(invoice, pelanggan, paket, deskripsi, pajak, no_telp)

    # With rate limiting:
    # result = await create_invoice_with_rate_limit(invoice, pelanggan, paket, deskripsi, pajak, no_telp)
    """

    return await rate_limiter.create_invoice_with_rate_limit(
        invoice, pelanggan, paket, deskripsi_xendit, pajak, no_telp_xendit, priority
    )


async def create_bulk_invoices_with_rate_limit(invoices_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Convenience function untuk bulk invoice creation dengan rate limiting.

    Args:
        invoices_data: List of dictionaries dengan format:
        {
            'invoice': InvoiceModel,
            'pelanggan': PelangganModel,
            'paket': PaketLayananModel,
            'deskripsi_xendit': str,
            'pajak': float,
            'no_telp_xendit': str (optional),
            'priority': InvoicePriority (optional)
        }
    """

    return await rate_limiter.create_bulk_invoices_with_rate_limit(invoices_data)