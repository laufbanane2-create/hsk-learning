package com.laufbanane2.hsklearning.ui.settings

import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.RectF
import android.util.AttributeSet
import android.view.View

/**
 * Draws a cascaded (concentric-ring) pie chart.
 *
 * Each [RingData] entry becomes one ring, drawn from outermost (index 0) to
 * innermost (last index).  Every ring is divided into three arc segments:
 *   - NEW        → grey
 *   - IN_PROGRESS → amber
 *   - MATURE     → green
 *
 * A legend row is rendered below the chart.
 */
class PieChartView @JvmOverloads constructor(
    context: Context,
    attrs: AttributeSet? = null,
    defStyle: Int = 0
) : View(context, attrs, defStyle) {

    data class RingData(
        val label: String,
        val newCount: Int,
        val inProgressCount: Int,
        val matureCount: Int
    )

    private val rings = mutableListOf<RingData>()

    private val colorNew        = Color.parseColor("#9E9E9E")
    private val colorInProgress = Color.parseColor("#FFA726")
    private val colorMature     = Color.parseColor("#4CAF50")
    private val colorEmpty      = Color.parseColor("#E0E0E0")
    private val colorLabel      = Color.parseColor("#212121")
    private val colorLegendText = Color.parseColor("#424242")

    private val arcPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply { style = Paint.Style.STROKE }
    private val labelPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = colorLabel
        textAlign = Paint.Align.CENTER
        isFakeBoldText = true
    }
    private val legendDotPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply { style = Paint.Style.FILL }
    private val legendTextPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = colorLegendText
        textAlign = Paint.Align.LEFT
    }

    // Gap between rings as a fraction of stroke width.
    private val gapFraction = 0.25f

    fun setRings(data: List<RingData>) {
        rings.clear()
        rings.addAll(data)
        requestLayout()
        invalidate()
    }

    // Legend entries: colour + label
    private val legendEntries by lazy {
        listOf(
            colorNew        to "New",
            colorInProgress to "In progress",
            colorMature     to "Mature"
        )
    }

    override fun onMeasure(widthMeasureSpec: Int, heightMeasureSpec: Int) {
        val w = MeasureSpec.getSize(widthMeasureSpec)
        // Chart is square; add room for the legend below.
        val legendHeight = (legendRowHeight() * legendEntries.size + legendTopMargin()).toInt()
        setMeasuredDimension(w, w + legendHeight)
    }

    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)
        if (rings.isEmpty()) return

        val w = width.toFloat()
        val n = rings.size

        // Reserve the top-square area for the chart.
        val chartSize = w
        val cx = chartSize / 2f
        val cy = chartSize / 2f

        // Divide the radius into n rings with equal stroke + gap widths.
        val totalRadius = chartSize / 2f - paddingLeft - 2f
        val strokeWidth = totalRadius / (n * (1f + gapFraction))
        val gap = strokeWidth * gapFraction

        arcPaint.strokeWidth = strokeWidth
        labelPaint.textSize = (strokeWidth * 0.38f).coerceAtLeast(10f)

        rings.forEachIndexed { i, ring ->
            // Outer ring has the largest radius.
            val radius = totalRadius - i * (strokeWidth + gap) - strokeWidth / 2f
            val oval = RectF(cx - radius, cy - radius, cx + radius, cy + radius)
            val total = ring.newCount + ring.inProgressCount + ring.matureCount

            if (total == 0) {
                arcPaint.color = colorEmpty
                canvas.drawOval(oval, arcPaint)
            } else {
                val degreesNew  = 360f * ring.newCount        / total
                val degreesProg = 360f * ring.inProgressCount / total
                val degreesMat  = 360f * ring.matureCount     / total

                // Draw segments (start from top: -90°)
                var startAngle = -90f
                if (ring.newCount > 0) {
                    arcPaint.color = colorNew
                    canvas.drawArc(oval, startAngle, degreesNew, false, arcPaint)
                    startAngle += degreesNew
                }
                if (ring.inProgressCount > 0) {
                    arcPaint.color = colorInProgress
                    canvas.drawArc(oval, startAngle, degreesProg, false, arcPaint)
                    startAngle += degreesProg
                }
                if (ring.matureCount > 0) {
                    arcPaint.color = colorMature
                    canvas.drawArc(oval, startAngle, degreesMat, false, arcPaint)
                }
            }

            // Ring label drawn to the left of the ring.
            val labelX = cx - radius - strokeWidth / 2f - 4f
            val labelY = cy + labelPaint.textSize / 3f
            labelPaint.textAlign = Paint.Align.RIGHT
            canvas.drawText(ring.label, labelX, labelY, labelPaint)
        }

        // Legend below the chart
        val dotRadius = legendDotRadius()
        val legendY0 = chartSize + legendTopMargin()
        val rowH = legendRowHeight()
        legendEntries.forEachIndexed { idx, (color, text) ->
            legendDotPaint.color = color
            val dotX = paddingLeft + dotRadius + 4f
            val dotY = legendY0 + idx * rowH + rowH / 2f
            canvas.drawCircle(dotX, dotY, dotRadius, legendDotPaint)
            legendTextPaint.textSize = rowH * 0.55f
            canvas.drawText(text, dotX + dotRadius + 8f, dotY + legendTextPaint.textSize / 3f, legendTextPaint)
        }
    }

    private fun legendDotRadius() = 8f * resources.displayMetrics.density
    private fun legendRowHeight() = 28f * resources.displayMetrics.density
    private fun legendTopMargin() = 12f * resources.displayMetrics.density
}
