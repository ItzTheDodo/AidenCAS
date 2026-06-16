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

    draw() {}

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

    update() {
        for (let graph of this.graphs) {
            if (!graph.getIsVisible()) {
                continue
            }

            graph.draw?.()
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

function addFunctionOption(_) {
    let count = document.getElementsByClassName("function_input_box").length
    let new_div = document.createElement("div")
    new_div.classList.add("function_input_box")
    new_div.id = `function_input_box_${count}`
    new_div.innerHTML = `
    <div class="function_input_container">
        <div class="function_display_button" id="function_display_button_${count}"></div>
        <input class="function_input" id="function_input_${count}" type="text" />
    </div>
    <p class="function_input_error" id="function_input_error_${count}"></p>`

    document.getElementById("add_function_box").before(new_div)
    document.getElementById(`function_input_${count}`).addEventListener("change", function() {
        defineFunction(count, document.getElementById(`function_input_${count}`).value)
    })
    document.getElementById(`function_display_button_${count}`).addEventListener("click", function() {
        display.toggleGraphVisibility(count)
    })

    defineFunction(count, document.getElementById(`function_input_${count}`).value)
    document.getElementById(`function_display_button_${count}`).classList.add("function_display_button_active")

}
