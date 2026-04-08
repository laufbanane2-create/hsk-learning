package com.laufbanane2.hsklearning.ui.settings

import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.RectF
import android.util.AttributeSet
import android.view.View

/**
 * Draws a single standard pie chart (filled wedges) for one HSK category.
 *
 * Three segments:
 *   - NEW        → grey   (#9E9E9E)
 *   - IN_PROGRESS → amber  (#FFA726)
 *   - MATURE     → green  (#4CAF50)
 *
 * A title label is drawn centred below the pie, followed by a compact legend.
 * Call [setData] to populate the chart; the view re-draws itself automatically.
 */
class PieChartView @JvmOverloads constructor(
    context: Context,
    attrs: AttributeSet? = null,
    defStyle: Int = 0
) : View(context, attrs, defStyle) {

    data class SliceData(
        val label: String,
        val newCount: Int,
        val inProgressCount: Int,
        val matureCount: Int
    )

    private var data: SliceData? = null

    private val colorNew        = Color.parseColor("#9E9E9E")
    private val colorInProgress = Color.parseColor("#FFA726")
    private val colorMature     = Color.parseColor("#4CAF50")
    private val colorEmpty      = Color.parseColor("#E0E0E0")
    private val colorTitle      = Color.parseColor("#212121")
    private val colorLegendText = Color.parseColor("#424242")

    private val slicePaint  = Paint(Paint.ANTI_ALIAS_FLAG).apply { style = Paint.Style.FILL }
    private val titlePaint  = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = colorTitle
        textAlign = Paint.Align.CENTER
        isFakeBoldText = true
    }
    private val dotPaint    = Paint(Paint.ANTI_ALIAS_FLAG).apply { style = Paint.Style.FILL }
    private val legendPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = colorLegendText
        textAlign = Paint.Align.LEFT
    }

    private val legendEntries = listOf(
        colorNew        to "New",
        colorInProgress to "In progress",
        colorMature     to "Mature"
    )

    fun setData(sliceData: SliceData) {
        data = sliceData
        requestLayout()
        invalidate()
    }

    private fun dp(value: Float) = value * resources.displayMetrics.density

    private fun titleHeight()    = dp(20f)
    private fun legendRowHeight()= dp(22f)
    private fun legendTopMargin()= dp(8f)
    private fun titleTopMargin() = dp(6f)

    override fun onMeasure(widthMeasureSpec: Int, heightMeasureSpec: Int) {
        val w = MeasureSpec.getSize(widthMeasureSpec)
        val extraHeight = (titleTopMargin() + titleHeight() +
                legendTopMargin() + legendRowHeight() * legendEntries.size).toInt()
        setMeasuredDimension(w, w + extraHeight)
    }

    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)
        val d = data ?: return

        val w = width.toFloat()
        val pieSize = w
        val padding = dp(4f)
        val oval = RectF(padding, padding, pieSize - padding, pieSize - padding)
        val total = d.newCount + d.inProgressCount + d.matureCount

        if (total == 0) {
            slicePaint.color = colorEmpty
            canvas.drawOval(oval, slicePaint)
        } else {
            var startAngle = -90f
            val slices = listOf(
                d.newCount        to colorNew,
                d.inProgressCount to colorInProgress,
                d.matureCount     to colorMature
            )
            slices.forEach { (count, color) ->
                if (count > 0) {
                    val sweep = 360f * count / total
                    slicePaint.color = color
                    canvas.drawArc(oval, startAngle, sweep, true, slicePaint)
                    startAngle += sweep
                }
            }
        }

        // Title below the pie
        val titleSize = dp(13f)
        titlePaint.textSize = titleSize
        val titleY = pieSize + titleTopMargin() + titleSize
        canvas.drawText(d.label, w / 2f, titleY, titlePaint)

        // Legend rows
        val dotRadius = dp(5f)
        val rowH = legendRowHeight()
        val legendY0 = titleY + legendTopMargin() + rowH * 0.1f
        legendPaint.textSize = dp(11f)
        legendEntries.forEachIndexed { idx, (color, text) ->
            dotPaint.color = color
            val rowCy = legendY0 + idx * rowH + rowH / 2f
            val dotX = padding + dotRadius
            canvas.drawCircle(dotX, rowCy, dotRadius, dotPaint)
            canvas.drawText(text, dotX + dotRadius + dp(5f), rowCy + dp(4f), legendPaint)
        }
    }
}

