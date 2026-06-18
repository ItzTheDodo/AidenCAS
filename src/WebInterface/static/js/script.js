"use strict";


class Graph {

    constructor(input_id, name) {
        this.input_id = input_id
        this.name = name
        this.is_visible = true
    }

    getInputId() {
        return this.input_id
    }

    getName() {
        return this.name
    }

    setName(name) {
        this.name = name
    }

    getIsVisible() {
        return this.is_visible
    }

    toggleVisible() {
        this.setVisible(!this.is_visible)
        return this.is_visible
    }

    setVisible(is_visible) {
        this.is_visible = is_visible
        if (this.is_visible) {
            document.getElementById(`function_display_button_${this.getInputId()}`).classList.remove("function_display_button_active")
        } else {
            document.getElementById(`function_display_button_${this.getInputId()}`).classList.add("function_display_button_active")
        }
    }

    async getValueAtPoint(num) {
        try {
            let data = await $.ajax({
                type: "GET",
                dataType: "json",
                url: "http://localhost:8080/evaluate",
                data: {name: this.getName(), point: num},
            });

            if (!data.ok) {
                console.log("Error fetching value at point: " + data.error)
                return [data.ok, data.error]
            }

            return [data.ok, data.result]

        } catch (e) {
            console.log("Error fetching value at point: " + e.message)
            return [false, e]
        }
    }

    async batchEvaluate(points) {
        try {
            let data = await $.ajax({
                type: "GET",
                dataType: "json",
                url: "http://localhost:8080/batch_evaluate",
                data: {name: this.getName(), points: JSON.stringify(points)},
            })

            if (!data.ok) {
                console.log("Error fetching value at point: " + data.error)
                return [data.ok, data.error]
            }

            return [data.ok, data.results]
        } catch (e) {
            console.log("Error fetching value at point: " + e.message)
            return [false, e]
        }
    }

    getGraphColour() {
        return document.getElementById(`function_input_${this.getInputId()}`).style.color
    }

    async draw(ctx, resolution, scale) {
        let gapx_num = (scale[0][1] - scale[0][0]) / resolution
        let gapx_px = ctx.canvas.width / (scale[0][1] - scale[0][0])
        let gapy_px = ctx.canvas.height / (scale[1][1] - scale[1][0]) // gap between numbers on y-axis

        let prev_y_axis_pos = null
        let prev_x_axis_pos = null

        ctx.strokeStyle = this.getGraphColour()
        ctx.lineWidth = 2

        let points_to_evaluate = []

        for (let i = 0; i < resolution; i++) {
            points_to_evaluate.push(scale[0][0] + gapx_num * i)
        }
        let [ok, results] = await this.batchEvaluate(points_to_evaluate)

        if (!ok) {
            console.log("Error fetching values for graph: " + results)
            return
        }


        for (let i = 0; i < resolution; i++) {
            let num = points_to_evaluate[i]
            let result = results[i]
            if (result === undefined) {
                continue
            }
            if (result === null) {
                result = 0
            }

            let x_axis_pos = (num - scale[0][0]) * gapx_px
            let y_axis_pos = ctx.canvas.height - (result - scale[1][0]) * gapy_px

            if (prev_x_axis_pos === null || prev_y_axis_pos === null) {
                prev_x_axis_pos = x_axis_pos
                prev_y_axis_pos = y_axis_pos
                continue
            }

            ctx.beginPath()
            ctx.moveTo(prev_x_axis_pos, prev_y_axis_pos)
            ctx.lineTo(x_axis_pos, y_axis_pos)
            ctx.stroke()

            prev_x_axis_pos = x_axis_pos
            prev_y_axis_pos = y_axis_pos
        }

    }

}


class Display {

    constructor(ctx) {
        this.scale = [[-10, 10], [-10, 10]]  // [x-min, x-max], [y-min, y-max]
        this.resolution = 1000 // number of points to be calculated for each graph on the scale interval
        this.graphs = []  // all graphs to be displayed
        this.ctx = ctx
    }

    setXmin(min) {
        this.scale[0][0] = min
        this.verifyScale()
    }

    setXmax(max) {
        this.scale[0][1] = max
        this.verifyScale()
    }

    setYmin(min) {
        this.scale[1][0] = min
        this.verifyScale()
    }

    setYmax(max) {
        this.scale[1][1] = max
        this.verifyScale()
    }

    getXmin() {
        return this.scale[0][0]
    }

    getXmax() {
        return this.scale[0][1]
    }

    getYmin() {
        return this.scale[1][0]
    }

    getYmax() {
        return this.scale[1][1]
    }

    verifyScale() {
        if (this.getXmin() >= this.getXmax()) {
            let t = this.getXmin()
            this.setXmin(this.getXmax())
            this.setXmax(t)
        }
        if (this.getYmin() >= this.getYmax()) {
            let t = this.getYmin()
            this.setYmin(this.getYmax())
            this.setYmax(t)
        }
    }

    syncVisibilityButton(graph) {
        const button = document.getElementById(`function_display_button_${graph.getInputId()}`)

        if (!button) {
            return
        }

        if (graph.getIsVisible()) {
            button.classList.remove("function_display_button_active")
        } else {
            button.classList.add("function_display_button_active")
        }
    }

    toggleGraphVisibility(input_id) {
        const graph = this.getGraphByInputId(input_id)

        if (!graph) {
            return
        }

        graph.toggleVisible()
        this.syncVisibilityButton(graph)
        this.update()
    }

    addGraph(input_id, name) {
        for (let graph of this.graphs) {
            if (graph.getInputId() === input_id) {
                graph.setName(name)
                this.syncVisibilityButton(graph)
                return
            }
        }

        let graph = new Graph(input_id, name)
        this.graphs.push(graph)
        this.syncVisibilityButton(graph)
    }

    _findSuitableLineGapx() {
        let objective_lines = 20

        let objective_distx = this.ctx.canvas.width / objective_lines
        let num_distx = this.getXmax() - this.getXmin()
        let gapx = 1

        while (num_distx / gapx > objective_distx) {
            gapx *= 2
        }

        return [gapx, gapx * (this.ctx.canvas.width / (this.getXmax() - this.getXmin()))]
    }

    _findSuitableLineGapy() {
        let objective_lines = 20

        let objective_disty = this.ctx.canvas.height / objective_lines
        let num_disty = this.getYmax() - this.getYmin()
        let gapy = 1

        while (num_disty / gapy > objective_disty) {
            gapy *= 5
        }

        return [gapy, gapy * (this.ctx.canvas.height / (this.getYmax() - this.getYmin()))]
    }

    async update() {

        this.ctx.clearRect(0, 0, this.ctx.canvas.width, this.ctx.canvas.height) // clear canvas
        this.ctx.fillStyle = "#F0F0F0"
        this.ctx.fillRect(0, 0, this.ctx.canvas.width, this.ctx.canvas.height);


        let linecol = "#C0C0FF"
        let major_line_width = 4
        let minor_line_width = 1

        let sx = this._findSuitableLineGapx()
        let sy = this._findSuitableLineGapy()
        let gapx_num = sx[0]
        let gapy_num = sy[0]
        let gapx_px = sx[1]
        let gapy_px = sy[1]

        this.ctx.strokeStyle = linecol
        this.ctx.lineWidth = major_line_width

        this.ctx.fillStyle = "#000000"
        this.ctx.font = "12px arial"
        this.ctx.textAlign = "center"
        this.ctx.textBaseline = "middle"

        // draw x-axis
        let y_axis_pos = this.ctx.canvas.height * (this.getYmax() / (this.getYmax() - this.getYmin()))
        this.ctx.beginPath()
        this.ctx.moveTo(0, y_axis_pos)
        this.ctx.lineTo(this.ctx.canvas.width, y_axis_pos)
        this.ctx.stroke()

        // draw y-axis
        let x_axis_pos = this.ctx.canvas.width * (-this.getXmin() / (this.getXmax() - this.getXmin()))
        this.ctx.beginPath()
        this.ctx.moveTo(x_axis_pos, 0)
        this.ctx.lineTo(x_axis_pos, this.ctx.canvas.height)
        this.ctx.stroke()

        this.ctx.lineWidth = minor_line_width

        let i = gapx_px
        let numx = this.getXmin() + gapx_num
        while (i < this.ctx.canvas.width) {
            this.ctx.beginPath()
            this.ctx.moveTo(i, 0)
            this.ctx.lineTo(i, this.ctx.canvas.height)
            this.ctx.stroke()
            if (numx !== 0) {
                this.ctx.fillText(numx.toString(), i, y_axis_pos + 15)
            }
            numx += gapx_num
            i += gapx_px
        }

        let k = gapy_px
        let numy = this.getYmax() - gapy_num
        while (k < this.ctx.canvas.height) {
            this.ctx.beginPath()
            this.ctx.moveTo(0, k)
            this.ctx.lineTo(this.ctx.canvas.width, k)
            this.ctx.stroke()
            this.ctx.fillText(numy.toString(), x_axis_pos - 10, k)
            numy -= gapy_num
            k += gapy_px
        }

        console.log(this.graphs)

        for (let graph of this.graphs) {
            if (!graph.getIsVisible()) {
                continue
            }

            console.log("Drawing graph: " + graph.getName())

            await graph.draw(this.ctx, this.resolution, this.scale).then(r => {})
        }
    }

    getGraphByInputId(input_id) {
        return this.graphs.find(graph => graph.getInputId() === input_id)
    }
}

const graphic_canvas = document.getElementById("graphic_display")
const ctx = graphic_canvas.getContext("2d")
const display = new Display(ctx)

async function defineFunction(input_id, definition) {
    const input = document.getElementById(`function_input_${input_id}`)
    const errorElement = document.getElementById(`function_input_error_${input_id}`)


    input.classList.remove("function_input_has_error")
    errorElement.textContent = ""

    try {
        let data = await $.ajax({
           type: "GET",
           dataType: "json",
           url: "http://localhost:8080/define_function",
           data: {definition: definition},
        });

        if (!data.ok) {
            errorElement.innerText = data.name
            input.classList.add("function_input_has_error")
            return
        }
        display.addGraph(input_id, data.name)
        errorElement.innerText = ""
        input.classList.remove("function_input_has_error")

    } catch (xhr) {
        input.classList.add("function_input_has_error")

        const response = xhr.responseJSON

        if (response) {
            errorElement.textContent = response.error || response.name || "Request failed."
        } else {
            errorElement.textContent = "Could not connect to the server."
        }
    }
}

async function updateAllFunctions() {
    for (let i = 0; i < document.getElementsByClassName("function_input").length; i++) {
        await defineFunction(i, document.getElementById(`function_input_${i}`).value)
    }
}

function addFunctionOption(_) {

    let assigned_colour = '#'+(Math.random() * 0xFFFFFF << 0).toString(16).padStart(6, '0');
    let count = document.getElementsByClassName("function_input_box").length
    let new_div = document.createElement("div")
    new_div.classList.add("function_input_box")
    new_div.id = `function_input_box_${count}`
    new_div.innerHTML = `
    <div class="function_input_container">
        <div class="function_display_button" id="function_display_button_${count}"></div>
        <input class="function_input" id="function_input_${count}" type="text" style="color: ${assigned_colour}!important;" />
    </div>
    <p class="function_input_error" id="function_input_error_${count}"></p>`

    document.getElementById("add_function_box").before(new_div)
    document.getElementById(`function_input_${count}`).addEventListener("input", async function() {
            await updateAllFunctions()
            await display.update()
        })
    document.getElementById(`function_display_button_${count}`).addEventListener("click", function() {
        display.toggleGraphVisibility(count)
    })

    defineFunction(count, document.getElementById(`function_input_${count}`).value)
    document.getElementById(`function_display_button_${count}`).classList.add("function_display_button_active")

}

window.addEventListener("resize", async function () {
    graphic_canvas.width = window.visualViewport.width - document.getElementById("sidebar").clientWidth
    graphic_canvas.height = window.visualViewport.height - (document.getElementById("header").clientHeight + document.getElementById("footer").clientHeight)
    await display.update()
})

addFunctionOption() // add single option to start
graphic_canvas.width = window.visualViewport.width - document.getElementById("sidebar").clientWidth
graphic_canvas.height = window.visualViewport.height - (document.getElementById("header").clientHeight + document.getElementById("footer").clientHeight)
display.update().then(_ => {})
