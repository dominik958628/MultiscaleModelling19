<template lang="pug">
  .page
    .view
      h1 Simulation view
      img(ref="img" @click="imgclick")
      img(ref="boundaries" @click="imgclick")
      div(v-if="showBoundaries && space.boundaries") Boundary percentage: {{space.boundaries && space.boundaries.percentage}}
      br
      div(v-if="selection.length")
        img(ref="selImg" @click="imgclick")
        img(ref="selBoundaries" @click="imgclick")
    h1 Simulation settings and controls
    h2 Simulation control
    a-form-item(label="Simulation" :label-col="{ span: 5 }" :wrapper-col="{ span: 12 }")
      a-button(v-if="simulating" type="primary" @click="simulating=false" icon="pause") Stop
      a-button(v-else @click="start" type="primary" icon="caret-right") Start
      a-button(@click="step" icon="step-forward") Step
    h2 Boundaries
    a-form-item(label="Show boundaries" :label-col="{ span: 5 }" :wrapper-col="{ span: 12 }")
      a-switch(v-model="showBoundaries" @change="reloadSpace(space.json)")
    a-form-item(label="Boundary size" :label-col="{ span: 5 }" :wrapper-col="{ span: 12 }")
      a-input(v-model="boundariesSize_" @change="reloadSpace(space.json)" :disabled="!showBoundaries")
    h2 Random selection
    a-form-item(label="Actions" :label-col="{ span: 5 }" :wrapper-col="{ span: 12 }")
      a-button(type="primary" @click="randomSelection") Select randomly
    a-form-item(label="Amount" :label-col="{ span: 5 }" :wrapper-col="{ span: 12 }")
      a-input-number(v-model="selectionSize")
    h2 Space import/export
    a-form-item(label="Import/Export" :label-col="{ span: 5 }" :wrapper-col="{ span: 12 }")
      a-button(@click="downloadSpaceJson") Export space.json
      a-upload(:multiple="false" :beforeUpload="importSpaceJson" :showUploadList="false")
        a-button Import space.json
    a-form-item(label="Import image" :label-col="{ span: 5 }" :wrapper-col="{ span: 12 }")
      a-upload(:multiple="false" :beforeUpload="importSpaceImage" :showUploadList="false")
        a-button Import space.bmp
    h2 Space
    a-form-item(label="Generate space" :label-col="{ span: 5 }" :wrapper-col="{ span: 12 }")
      a-button(@click="generateSpace" type="primary") Generate space and nucleons
    a-form-item(label="Substructure and dual-phase" :label-col="{ span: 5 }" :wrapper-col="{ span: 12 }")
      a-button(@click="selectionToSpace") Use selected
      a-button(@click="spaceToInclusions") Change to phase
      a-button(@click="addNucleons") Add nucleons
    a-form-item(label="Actions related to boundaries" :label-col="{ span: 5 }" :wrapper-col="{ span: 12 }")
      a-button(@click="reloadSpace(space.boundaries.json); selection=[]") Space from boundaries
      a-button(@click="reloadSpace(space.selectedSpace.boundaries.json); selection=[]") Space from boundaries of selected grains
    a-form-item(label="Width x Height" :label-col="{ span: 5 }" :wrapper-col="{ span: 12 }")
      a-input-group(compact)
        a-input-number(v-model="width")
        a-input-number(v-model="height")
    a-form-item(label="Nucleons count" :label-col="{ span: 5 }" :wrapper-col="{ span: 12 }")
      a-input-number(v-model="seeds")
    h2 Boundary conditions
    a-form-item(label="Boundary" :label-col="{ span: 5 }" :wrapper-col="{ span: 12 }")
      a-radio-group(v-model="edge")
        a-radio-button(value="absorbing") Absorbing
        a-radio-button(value="repeating") Repeating
    h2 Rules
    a-form-item(label="Type" :label-col="{ span: 5 }" :wrapper-col="{ span: 12 }")
      a-radio-group(v-model="rulesType")
        a-radio-button(value="normal") Simple
        a-radio-button(value="advanced") Advanced
    a-form-item(label="Probability" :label-col="{ span: 5 }" :wrapper-col="{ span: 12 }")
      a-input-number(v-model="advancedProbability" :disabled="rulesType!=='advanced'")
    a-form-item(v-if="rulesType!=='advanced'" label="Neighbour" :label-col="{ span: 5 }" :wrapper-col="{ span: 12 }")
      a-select(v-model="neighborhoodKey")
        a-select-option(v-for="n in neighborhoods" :value="n.key" :key="n.key") {{n.name}}
      div
        svg.previewNeighbour(v-for="cells in neighborhood.cells" :width="cellSize*4*2" :height="cellSize*4*2")
          g(:transform="`translate(${cellSize*4-cellSize/2}, ${cellSize*4-cellSize/2})`")
            rect.main(:x="0+1" :y="0+1" :width="cellSize-2" :height="cellSize-2")
            rect(
              v-for="cell in cells"
              :x="cell[0]*cellSize+1" :y="cell[1]*cellSize+1"
              :width="cellSize-2" :height="cellSize-2"
            )
    h2 Inclusions
    a-form-item(label="Actions" :label-col="{ span: 5 }" :wrapper-col="{ span: 12 }")
      a-button(@click="addInclusions" type="primary") Add inclusions
    a-form-item(label="Position" :label-col="{ span: 5 }" :wrapper-col="{ span: 12 }")
      a-radio-group(v-model="inclusionsOnBoundary")
        a-radio-button(:value="false") Anywhere
        a-radio-button(:value="true") On bounaries
    a-form-item(label="Shape" :label-col="{ span: 5 }" :wrapper-col="{ span: 12 }")
      a-radio-group(v-model="inclusionType")
        a-radio-button(value="square") Square
        a-radio-button(value="circle") Circle
    a-form-item(label="Count" :label-col="{ span: 5 }" :wrapper-col="{ span: 12 }")
      a-input-number(v-model="inclusionsCount")
    a-form-item(label="Size" :label-col="{ span: 5 }" :wrapper-col="{ span: 12 }")
      a-input-number(v-model="inclusionsSize")
</template>

<script>
import gql from 'graphql-tag';

const NEIGHBORHOODS = [
  {
    key: 'Von Neumann',
    name: 'Von Neumann',
    cells: [
      [
        [-1, 0],
        [1, 0],
        [0, -1],
        [0, 1],
      ],
    ]
  },
  {
    key: 'Moore',
    name: 'Moore',
    cells: [
      [
        [-1, -1],
        [-1, 0],
        [-1, 1],
        [0, -1],
        [0, 1],
        [1, -1],
        [1, 0],
        [1, 1],
      ],
    ]
  },
  /*
  {
    key: 'Further Moore',
    name: 'Further Moore',
    cells: [
      [
        [-1, -1],
        [1, 1],
        [1, -1],
        [-1, 1],
      ],
    ]
  },
  {
    key: 'Extended Von Neumann',
    name: 'Extended Von Neumann',
    cells: [
      [
        [-2, 0],
        [2, 0],
        [0, -2],
        [0, 2],

        [-1, -1],
        [-1, 0],
        [-1, 1],
        [0, -1],
        [0, 1],
        [1, -1],
        [1, 0],
        [1, 1],
      ],
    ]
  },
  {
    key: 'Random hexagonal',
    name: 'Random hexagonal',
    cells: [
      [
        [-1, 0],
        [-1, 1],
        [0, -1],
        [0, 1],
        [1, -1],
        [1, 0],
      ],
      [
        [-1, -1],
        [-1, 0],
        [0, -1],
        [0, 1],
        [1, 0],
        [1, 1],
      ],
    ]
  },
  {
    key: 'Random pentagonal',
    name: 'Random pentagonal',
    cells: [
      [
        [-1, -1],
        [-1, 0],
        [-1, 1],
        [0, -1],
        [0, 1],
      ],
      [
        [0, -1],
        [0, 1],
        [1, -1],
        [1, 0],
        [1, 1],
      ],
      [
        [-1, 0],
        [-1, 1],
        [0, 1],
        [1, 0],
        [1, 1],
      ],
      [
        [-1, -1],
        [-1, 0],
        [0, -1],
        [1, -1],
        [1, 0],
      ]
    ]
  },
   */
];

// https://ourcodeworld.com/articles/read/189/how-to-create-a-file-and-generate-a-download-with-javascript-in-the-browser-without-a-server
function download(filename, text) {
  var element = document.createElement('a');
  element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(text));
  element.setAttribute('download', filename);

  element.style.display = 'none';
  document.body.appendChild(element);

  element.click();

  document.body.removeChild(element);
}

export default {
  data() {
    return {
      showBoundaries: false,
      boundariesSize_: '1',
      width: 300,
      height: 300,
      seeds: 50,
      add: 2,
      inclusionsCount: 10,
      inclusionsSize: 20,
      inclusionsOnBoundary: false,
      neighborhoods: NEIGHBORHOODS,
      neighborhood: NEIGHBORHOODS[0],
      edge: 'absorbing',
      cellSize: 20,
      rulesType: "normal",
      advancedProbability: 50,
      inclusionType: "circle",
      simulating: false,
      selection: [],
      selectionSize: 50,
      space: {
        json: undefined,
        dataUrl: '',
        selectedSpace: {
          dataUrl: '',
          boundaries: {
            dataUrl: ''
          }
        },
      },
    }
  },
  computed: {
    boundariesSize() {
      return Number(this.boundariesSize_);
    },
    neighborhoodKey: {
      get() {
        return this.neighborhood.key;
      },
      set(key) {
        this.neighborhood = NEIGHBORHOODS.find(n => n.key === key);
      }
    },
    rules() {
      return {
        rulesType: this.rulesType,
        cells: this.neighborhood.cells,
        advancedProbability: this.advancedProbability,
        edge: this.edge,
      }
    }
  },
  watch: {
    space(newSpace) {
      this.$refs.img.setAttribute("src", newSpace.dataUrl);
      this.$refs.boundaries.setAttribute("src", newSpace.boundaries.dataUrl);
      if(this.selection.length) {
        this.$refs.selImg.setAttribute("src", newSpace.selectedSpace.dataUrl);
        this.$refs.selBoundaries.setAttribute("src", newSpace.selectedSpace.boundaries.dataUrl);
      }
    },
  },
  methods: {
    async imgclick(event) {
      let r = await this.$apollo.query({
        query: gql`query($spaceJson: Json!, $selection: Selection!, $x: Int!, $y: Int!) {
          toggleSelection(spaceJson: $spaceJson, selection: $selection, x: $x, y: $y)
        }`,
        variables: {
          spaceJson: this.space.json,
          selection: this.selection,
          x: event.offsetX,
          y: event.offsetY,
        },
        fetchPolicy: 'no-cache',
      });
      this.selection = r.data.toggleSelection;
      console.log(this.selection);
      if(!this.simulating) {
        await this.reloadSpace(this.space.json);
      }
    },
    async randomSelection(event) {
      let r = await this.$apollo.query({
        query: gql`query($spaceJson: Json!, $selectionSize: Int!) {
          randomSelection(spaceJson: $spaceJson, size: $selectionSize)
        }`,
        variables: {
          spaceJson: this.space.json,
          selectionSize: this.selectionSize,
        },
        fetchPolicy: 'no-cache',
      });
      this.selection = r.data.randomSelection;
      console.log(this.selection);
      if(!this.simulating) {
        await this.reloadSpace(this.space.json);
      }
    },
    async generateSpace() {
      this.selection = [];
      let r = await this.$apollo.query({
        query: gql`query generateSpace($width: Int!, $height: Int!, $nucleons: Int!, $rules: Rules!, $selection: Selection!, $showBoundaries: Boolean!, $boundariesSize: Int!) {
          generateSpace(width: $width, height: $height, nucleons: $nucleons) {
            dataUrl,
            json,
            boundaries(rules: $rules, generate: $showBoundaries, size: $boundariesSize) {
              dataUrl
              json
              percentage
            }
            selectedSpace(selection: $selection) {
              dataUrl
              json
              boundaries(rules: $rules, generate: $showBoundaries, size: $boundariesSize) {
                dataUrl
                json
                percentage
              }
            }
          }
        }`,
        variables: {
          width: this.width,
          height: this.height,
          nucleons: this.seeds,
          rules: this.rules,
          selection: this.selection,
          showBoundaries: this.showBoundaries,
          boundariesSize: this.boundariesSize,
        },
        fetchPolicy: 'no-cache',
      });
      this.space = r.data.generateSpace;
      console.log(r.data)
    },
    async selectionToSpace() {
      this.selection = [];
      this.space = this.space.selectedSpace;
    },
    async addInclusions() {
      let r = await this.$apollo.query({
        query: gql`query addInlcusions(
          $spaceJson: Json!,
          $count: Int!,
          $type_: String!,
          $size: Int!,
          $onBoundary: Boolean!,
          $rules: Rules!,
          $selection: Selection!,
          $showBoundaries: Boolean!,
          $boundariesSize: Int!,
        ) {
          space: addInclusions(
            spaceJson: $spaceJson,
            count: $count,
            type_: $type_,
            size: $size,
            onBoundary: $onBoundary,
            rules: $rules,
          ) {
            dataUrl,
            json,
            boundaries(rules: $rules, generate: $showBoundaries, size: $boundariesSize) {
              dataUrl
              json
              percentage
            }
            selectedSpace(selection: $selection) {
              dataUrl
              json
              boundaries(rules: $rules, generate: $showBoundaries, size: $boundariesSize) {
                dataUrl
                json
                percentage
              }
            }
          }
        }`,
        variables: {
          spaceJson: this.space.json,
          count: this.inclusionsCount,
          type_: this.inclusionType,
          size: this.inclusionsSize,
          onBoundary: this.inclusionsOnBoundary,
          rules: this.rules,
          selection: this.selection,
          showBoundaries: this.showBoundaries,
          boundariesSize: this.boundariesSize,
        },
        fetchPolicy: 'no-cache',
      });
      this.space = r.data.space;
    },
    async step() {
      let r = await this.$apollo.query({
        query: gql`query addInlcusions(
          $spaceJson: Json!,
          $rules: Rules!,
          $selection: Selection!,
          $showBoundaries: Boolean!,
          $boundariesSize: Int!,
        ) {
          step(
            spaceJson: $spaceJson,
            rules: $rules,
          ) {
            newSpace {
              dataUrl,
              json,
              boundaries(rules: $rules, generate: $showBoundaries, size: $boundariesSize) {
                dataUrl
                json
                percentage
              }
              selectedSpace(selection: $selection) {
                dataUrl
                json
                boundaries(rules: $rules, generate: $showBoundaries, size: $boundariesSize) {
                  dataUrl
                  json
                  percentage
                }
              }
            }
          }
        }`,
        variables: {
          spaceJson: this.space.json,
          rules: this.rules,
          selection: this.selection,
          showBoundaries: this.showBoundaries,
          boundariesSize: this.boundariesSize,
        },
        fetchPolicy: 'no-cache',
      });
      this.space = r.data.step.newSpace;
    },
    async start() {
      this.simulating = true;
      let canChange = true;
      while(this.simulating && canChange) {
        let r = await this.$apollo.query({
          query: gql`query addInlcusions(
            $spaceJson: Json!,
            $rules: Rules!,
            $selection: Selection!,
            $showBoundaries: Boolean!,
            $boundariesSize: Int!,
          ) {
            step(
              spaceJson: $spaceJson,
              rules: $rules,
            ) {
              canChange,
              newSpace {
                dataUrl,
                json,
                boundaries(rules: $rules, generate: $showBoundaries, size: $boundariesSize) {
                  dataUrl
                  json
                  percentage
                }
                selectedSpace(selection: $selection) {
                  dataUrl
                  json
                  boundaries(rules: $rules, generate: $showBoundaries, size: $boundariesSize) {
                    dataUrl
                    json
                    percentage
                  }
                }
              }
            }
          }`,
          variables: {
            spaceJson: this.space.json,
            rules: this.rules,
            selection: this.selection,
            showBoundaries: this.showBoundaries,
            boundariesSize: this.boundariesSize,
          },
          fetchPolicy: 'no-cache',
        });
        this.space = r.data.step.newSpace;
        canChange = r.data.step.canChange;
      }
      this.simulating = false
    },
    downloadSpaceJson() {
      download("space.json", JSON.stringify(this.space.json));
    },
    async reloadSpace(spaceJson) {
      let r = await this.$apollo.query({
        query: gql`query addInlcusions(
          $spaceJson: Json!,
          $rules: Rules!,
          $selection: Selection!,
          $showBoundaries: Boolean!,
          $boundariesSize: Int!,
        ) {
          space: returnSpace(
            spaceJson: $spaceJson,
          ) {
            dataUrl,
            json,
            boundaries(rules: $rules, generate: $showBoundaries, size: $boundariesSize) {
              dataUrl
              json
              percentage
            }
            selectedSpace(selection: $selection) {
              dataUrl
              json
              boundaries(rules: $rules, generate: $showBoundaries, size: $boundariesSize) {
                dataUrl
                json
                percentage
              }
            }
          }
        }`,
        variables: {
          spaceJson: spaceJson,
          rules: this.rules,
          selection: this.selection,
          showBoundaries: this.showBoundaries,
          boundariesSize: this.boundariesSize,
        },
        fetchPolicy: 'no-cache',
      });
      this.space = r.data.space;
    },
    async spaceToInclusions() {
      let spaceJson = this.space.json;
      let r = await this.$apollo.query({
        query: gql`query(
            $spaceJson: Json!,
            $rules: Rules!,
            $selection: Selection!,
            $showBoundaries: Boolean!,
            $boundariesSize: Int!,
          ) {
            space: spaceToInclusions(
              spaceJson: $spaceJson,
            ) {
              dataUrl,
              json,
              boundaries(rules: $rules, generate: $showBoundaries, size: $boundariesSize) {
                dataUrl
                json
                percentage
              }
              selectedSpace(selection: $selection) {
                dataUrl
                json
                boundaries(rules: $rules, generate: $showBoundaries, size: $boundariesSize) {
                  dataUrl
                  json
                  percentage
                }
              }
            }
          }`,
        variables: {
          spaceJson: spaceJson,
          rules: this.rules,
          selection: this.selection,
          showBoundaries: this.showBoundaries,
          boundariesSize: this.boundariesSize,
        },
        fetchPolicy: 'no-cache',
      });
      this.space = r.data.space;
    },
    async addNucleons() {
      let spaceJson = this.space.json;
      let r = await this.$apollo.query({
        query: gql`query(
            $spaceJson: Json!,
            $rules: Rules!,
            $selection: Selection!,
            $count: Int!,
            $showBoundaries: Boolean!,
            $boundariesSize: Int!,
          ) {
            space: addNucleons(
              spaceJson: $spaceJson,
              count: $count,
            ) {
              dataUrl,
              json,
              boundaries(rules: $rules, generate: $showBoundaries, size: $boundariesSize) {
                dataUrl
                json
                percentage
              }
              selectedSpace(selection: $selection) {
                dataUrl
                json
                boundaries(rules: $rules, generate: $showBoundaries, size: $boundariesSize) {
                  dataUrl
                  json
                  percentage
                }
              }
            }
          }`,
        variables: {
          spaceJson: spaceJson,
          rules: this.rules,
          selection: this.selection,
          count: this.seeds,
          showBoundaries: this.showBoundaries,
          boundariesSize: this.boundariesSize,
        },
        fetchPolicy: 'no-cache',
      });
      this.space = r.data.space;
    },
    importSpaceJson(file) {
      // https://stackoverflow.com/a/29176118
      let reader = new FileReader();
      reader.onload = async () => {
        this.reloadSpace(JSON.parse(reader.result));
      };
      reader.readAsText(file);
      return false
    },
    async importSpaceImage(file) {
      // https://stackoverflow.com/a/29176118
      let reader = new FileReader();
      reader.onload = async () => {
        this.selection = [];
        let r = await this.$apollo.query({
          query: gql`query(
            $rules: Rules!,
            $selection: Selection!,
            $showBoundaries: Boolean!,
            $file: String!,
            $boundariesSize: Int!,
          ) {
            space: spaceFromFile(
              file: $file,
            ) {
              dataUrl,
              json,
              boundaries(rules: $rules, generate: $showBoundaries, size: $boundariesSize) {
                dataUrl
                json
                percentage
              }
              selectedSpace(selection: $selection) {
                dataUrl
                json
                boundaries(rules: $rules, generate: $showBoundaries, size: $boundariesSize) {
                  dataUrl
                  json
                  percentage
                }
              }
            }
          }`,
          variables: {
            rules: this.rules,
            selection: this.selection,
            showBoundaries: this.showBoundaries,
            boundariesSize: this.boundariesSize,
            file: reader.result,
          },
          fetchPolicy: 'no-cache',
        });
        this.space = r.data.space;
      };
      reader.readAsDataURL(file);
      return false
    }
  },
  mounted() {
    this.generateSpace();
  }
}
</script>

<style lang="scss" scoped>
.ant-form-item {
  margin-bottom: 6px;
}

.previewNeighbour {
  rect {
    fill: #303030;
  }
  rect.main {
    fill: #3b578b;
  }
}

.view {
  position: sticky;
  top: 0px;
  background-color: white;
  z-index: 100;
  padding-bottom: 1rem;
  border-bottom: 1px solid gray;
}
</style>
