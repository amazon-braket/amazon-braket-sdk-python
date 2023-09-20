---
sd_hide_title: true
---

# sphinx-design

::::::{div} landing-title
:style: "padding: 0.1rem 0.2rem 0.8rem 0.3rem; background-image: linear-gradient(0deg, #438ff9 0%, #1572f4 74%); clip-path: polygon(0px 0px, 100% 0%, 100% calc(100% - 1.5rem), 0% calc(100% - 1.5rem)); -webkit-clip-path: polygon(0px 0px, 100% 0%, 100% calc(100% - 1.5rem), 0% calc(100% - 1.5rem));"

::::{grid}
:reverse:
:gutter: 2 3 3 3
:margin: 4 4 1 2

:::{grid-item}
:columns: 12 4 4 4

```{image} ./_static/braket-avatar.png
:width: 200px
:class: sd-m-auto sd-animate-grow50-rot20
```
:::

:::{grid-item}
:columns: 12 8 8 8
:child-align: justify
:class: sd-text-white sd-fs-3

Amazon Braket Python SDK

```{button-ref} pages/setting_up
:ref-type: doc
:outline:
:color: white
:class: sd-px-4 sd-fs-5

Begin Setting Up
```

:::
::::

::::::

The **Amazon Braket Python SDK** is an open source library to design and build quantum circuits, submit them to Amazon Braket devices as quantum tasks, and monitor their execution.

This documentation provides information about the Amazon Braket Python SDK library. 

The project includes SDK source, installation instructions, and other information.

The project homepage is in [Github](https://github.com/aws/amazon-braket-sdk-python). 

```{toctree}
:hidden:
:caption: Setting Up

pages/setting_up
```

```{toctree}
:hidden:
:caption: SDK API Reference

_apidoc/modules
```

```{toctree}
:hidden:
:caption: Modules

pages/examples/getting_started
pages/examples/continue_exploring
pages/badge/braket_badge
pages/qbraid/getting_started_with_qbraid
```

```{toctree}
:hidden:
:caption: Pathways

pages/pathways/newcomer
pages/pathways/educator
pages/pathways/researcher
```

```{toctree}
:hidden:
:caption: Example Notebooks

pages/examples/getting_started
pages/examples/advanced_braket_features
pages/examples/applications_and_industry_uses
pages/examples/quantum_algorithms_and_protocols
pages/examples/quantum_frameworks_and_plugins
pages/examples/quantum_hardware
pages/examples/quantum_sims
```

::::{grid} 1 2 2 3
:margin: 4 4 0 0
:gutter: 1

:::{grid-item-card} {octicon}`chevron-right` Newcomers
:link: pages/pathways/newcomer
:link-type: doc

Recommended content for quantum newcomers.
:::

:::{grid-item-card} {octicon}`chevron-right` Researchers
:link: pages/pathways/researcher
:link-type: doc

Recommended content for quantum researchers.
:::

:::{grid-item-card} {octicon}`chevron-right` Educators
:link: pages/pathways/educator
:link-type: doc

Recommended content for quantum educators.
:::

:::{grid-item-card} {octicon}`chevron-right` Examples: Getting Started
:link: pages/examples/getting_started
:link-type: doc

Get familiarized with the Braket API through executable notebooks.
:::

:::{grid-item-card} {octicon}`chevron-right` Examples: Continue Exploring
:link: pages/examples/continue_exploring
:link-type: doc

Explore a variety of applications and features through executable notebooks.
:::

:::{grid-item-card} {octicon}`chevron-right` API Reference
:link: _apidoc/modules
:link-type: doc

:::

::::