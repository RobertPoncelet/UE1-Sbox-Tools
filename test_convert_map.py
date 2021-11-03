import datamodel as dmx

dm = dmx.load("test_input.vmap")
dm.write("test_output.vmap", "keyvalues2", 4)