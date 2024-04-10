# Process for updating the backend architecture diagram
The generation of the backend architecture diagram is partially automated. The diagram is generated from the type hints in the code using the py2puml tool. The diagram is then manually reviewed, adjusted and exported to PNG and SVG.

## Prerequisites
- Running python environment in which opendevin is executable (according to the instructions in the README.md file in the root of the repository)
- [py2puml](https://github.com/lucsorel/py2puml) installed

## Steps
1. Autogenerate the diagram by running the following command from the root of the repository:  
```py2puml opendevin opendevin > docs/architecture/backend_architecture.puml```

2. Open the generated file in a PlantUML editor, e.g. Visual Studio Code with the PlantUML extension or [PlantText](https://www.planttext.com/)

3. Review the generated PUML and make all necessary adjustments to the diagram (add missing parts, fix mistakes, improve positioning).  
*py2puml creates the diagram based on the type hints in the code, so missing or incorrect type hints may result in an incomplete or incorrect diagram.*

4. Review the diff between the new and the previous diagram and manually check if the changes are correct.  
*Make sure not to remove parts that were manually added to the diagram in the past and are still relevant.*

4. Add the commit hash of the commit that was used to generate the diagram to the diagram footer.

5. Export the diagram as PNG and SVG files and replace the existing diagrams in the `docs/architecture` directory. This can be done with (e.g. [PlantText](https://www.planttext.com/))

