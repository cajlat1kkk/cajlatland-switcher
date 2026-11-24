-- Release bindings for a modifier alone are cancelled by Hyprland when it
-- participates in a shortcut. Both bindings let the original key through.
local pending, generation = nil, 0
local presses = {}
local function command(signal)
    local units = "cajlatland-switcher.service"
    if signal == "USR1" then units = units .. " cajlatland-switcher-ibus.service" end
    hl.exec_cmd("systemctl --user kill --kill-whom=main --signal=" .. signal .. " " .. units)
end
for _, side in ipairs({"L", "R"}) do
    local key = "Shift_" .. side
    local opposite = side == "L" and "Shift_R" or "Shift_L"
    hl.bind(side == "L" and "code:50" or "code:62", function()
        generation = generation + 1
        local token = generation
        presses[key] = token
        if hl.is_key_down(opposite) then
            presses = {}
            pending = nil
            command("USR2")
        else
            hl.timer(function()
                if presses[key] == token then presses[key] = nil end
            end, {timeout=200, type="oneshot"})
        end
    end, { non_consuming=true, ignore_mods=true, description="Switcher · Нажатие Shift" })
    hl.bind(key, function()
        if not presses[key] then return end
        presses[key] = nil
        if pending then
            pending = nil
            command("USR1")
        else
            local runtime = os.getenv("XDG_RUNTIME_DIR")
            -- r+ avoids blocking the compositor if the service has stopped.
            -- Check existence first: io.open("r+") never creates the FIFO.
            local pipe = runtime and io.open(runtime .. "/cajlatland-switcher.shift", "r+")
            if pipe then
                pipe:write("s")
                pipe:close()
            end
            local ticket = {}
            pending = ticket
            hl.timer(function()
                if pending == ticket then
                    pending = nil
                end
            end, {timeout=300, type="oneshot"})
        end
    end, { release=true, non_consuming=true, description="Switcher · Короткое нажатие Shift" })
end
