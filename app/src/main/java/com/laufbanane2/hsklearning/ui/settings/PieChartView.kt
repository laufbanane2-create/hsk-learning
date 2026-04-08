package com.laufbanane2.hsklearning.ui.settings

import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.RectF
import android.util.AttributeSet
import android.view.View

/**
 * Draws a single standard pie chart (filled wedges).
 *
 * Call [setData] with a title and a list of [Entry] items to populate the chart.
 * Each entry contributes one coloured wedge and one legend row.
 * The view re-measures and redraws itself automatically.
 */
class PieChartView @JvmOverloads constructor(
    context: Context,
    attrs: AttributeSet? = null,
    defStyle: Int = 0
) : View(context, attrs, defStyle) {

    /** One slice in the pie chart. */
    data class Entry(val label: String, val color: Int, val count: Int)

    private var chartTitle: String = ""
    private var entries: List<Entry> = emptyList()

    private val colorEmpty      = Color.parseColor("#E0E0E0")
    private val colorTitle      = Color.parseColor("#212121")
    private val colorLegendText = Color.parseColor("#424242")

    private val slicePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply { style = Paint.Style.FILL }
    private val titlePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = colorTitle
        textAlign = Paint.Align.CENTER
        isFakeBoldText = true
    }
    private val dotPaint   = Paint(Paint.ANTI_ALIAS_FLAG).apply { style = Paint.Style.FILL }
    private val legendPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = colorLegendText
        textAlign = Paint.Align.LEFT
    }

    fun setData(title: String, entries: List<Entry>) {
        chartTitle = title
        this.entries = entries
        requestLayout()
        invalidate()
    }

    private fun dp(value: Float) = value * resources.displayMetrics.density

    private fun titleHeight()     = dp(20f)
    private fun legendRowHeight() = dp(22f)
    private fun legendTopMargin() = dp(8f)
    private fun titleTopMargin()  = dp(6f)

    override fun onMeasure(widthMeasureSpec: Int, heightMeasureSpec: Int) {
        val w = MeasureSpec.getSize(widthMeasureSpec)
        if (entries.isEmpty()) {
            setMeasuredDimension(w, 0)
            return
        }
        val extraHeight = (titleTopMargin() + titleHeight() +
                legendTopMargin() + legendRowHeight() * entries.size).toInt()
        setMeasuredDimension(w, w + extraHeight)
    }

    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)
        if (entries.isEmpty()) return

        val w = width.toFloat()
        val pieSize = w
        val padding = dp(4f)
        val oval = RectF(padding, padding, pieSize - padding, pieSize - padding)
        val total = entries.sumOf { it.count }

        if (total == 0) {
            slicePaint.color = colorEmpty
            canvas.drawOval(oval, slicePaint)
        } else {
            var startAngle = -90f
            entries.forEach { entry ->
                if (entry.count > 0) {
                    val sweep = 360f * entry.count / total
                    slicePaint.color = entry.color
                    canvas.drawArc(oval, startAngle, sweep, true, slicePaint)
                    startAngle += sweep
                }
            }
        }

        // Title below the pie
        val titleSize = dp(13f)
        titlePaint.textSize = titleSize
        val titleY = pieSize + titleTopMargin() + titleSize
        canvas.drawText(chartTitle, w / 2f, titleY, titlePaint)

        // Legend rows
        val dotRadius = dp(5f)
        val rowH = legendRowHeight()
        val legendY0 = titleY + legendTopMargin() + rowH * 0.1f
        legendPaint.textSize = dp(11f)
        entries.forEachIndexed { idx, entry ->
            dotPaint.color = entry.color
            val rowCy = legendY0 + idx * rowH + rowH / 2f
            val dotX = padding + dotRadius
            canvas.drawCircle(dotX, rowCy, dotRadius, dotPaint)
            canvas.drawText(entry.label, dotX + dotRadius + dp(5f), rowCy + dp(4f), legendPaint)
        }
    }
}

