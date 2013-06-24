import numpy as np


class DendrogramPlotter(object):

    """
    A class to plot a dendrogram object
    """

    def __init__(self, dendrogram):
        # should we copy to ensure immutability?
        self.dendrogram = dendrogram
        self._cached_positions = None
        self.sort()

    def sort(self, sort_key=lambda s: s.get_peak(subtree=True)[1], reverse=False):
        """
        Sort the position of the leaves for plotting

        Parameters
        ----------
        sort_key : function, optional
             This should be a function that takes a
             `~astrodendro.structure.Structure` and returns a scalar that is
             then used to sort the leaves.
        reverse : bool, optional
             Whether to reverse the sorting
        """

        sorted_trunk_structures = sorted(self.dendrogram.trunk, key=sort_key, reverse=reverse)

        positions = {}
        x = 0  # the first index for each trunk structure
        for structure in sorted_trunk_structures:

            # Get sorted leaves
            sorted_leaves = structure.get_sorted_leaves(subtree=True, reverse=reverse)

            # Loop over leaves and assign positions
            for leaf in sorted_leaves:
                positions[leaf] = x
                x += 1

            # Sort structures from the top-down
            sorted_structures = sorted(structure.descendants, key=lambda s: s.level, reverse=True) + [structure]

            # Loop through structures and assing position of branches as the mean
            # of the leaves
            for structure in sorted_structures:
                if not structure.is_leaf:
                    positions[structure] = np.mean([positions[child] for child in structure.children])

        self._cached_positions = positions

    def plot_tree(self, ax, structure=None, subtree=True, autoscale=True, **kwargs):
        """
        Plot the dendrogram tree or a substructure

        Parameters
        ----------
        ax : `matplotlib.axes.Axes` instance
            The Axes inside which to plot the dendrogram
        structure : int or `~astrodendro.structure.Structure`, optional
            If specified, only plot this structure
        subtree : bool, optional
            If a structure is specified, by default the whole subtree will be
            plotted, but this can be disabled with this option.
        autoscale : bool, optional
            Whether to automatically adapt the window limits to the tree

        Notes
        -----
        Any additional keyword arguments are passed to
        `~matplotlib.collections.LineCollection` and can be used to control the
        appearance of the plot.
        """

        # Get the lines for the dendrogram
        lines = self.get_lines(structure=structure, **kwargs)

        # Add the lines to the axes
        ax.add_collection(lines)

        # Auto-scale axes (doesn't happen by default with ``add_collection``)
        if autoscale:
            ax.margins(0.05)
            ax.autoscale_view(True, True, True)

    def get_lines(self, structure=None, **kwargs):
        """
        Get a collection of lines to draw the dendrogram

        Parameters
        ----------
        structure : `~astrodendro.structure.Structure`
            The structure to plot. If not set, the whole tree will be plotted.

        Returns
        -------
        lines : `astrodendro.plot.StructureCollection`
            The lines (sub-class of LineCollection) which can be directly used in Matplotlib

        Notes
        -----
        Any additional keyword arguments are passed to the
        `~matplotlib.collections.LineCollection` class.
        """

        if self._cached_positions is None:
            raise Exception("Leaves have not yet been sorted")

        if structure is None:
            structures = self.dendrogram.all_nodes
        else:
            if type(structure) is int:
                structure = self.dendrogram.nodes_dict[structure]
            structures = structure.descendants + [structure]

        lines = []
        mapping = []
        for s in structures:
            x = self._cached_positions[s]
            bot = s.parent.height if s.parent is not None else s.vmin
            top = s.height
            lines.append(([x, bot], [x, top]))
            mapping.append(s)
            if s.is_branch:
                pc = [self._cached_positions[c] for c in s.children]
                lines.append(([min(pc), top], [max(pc), top]))
                mapping.append(s)

        from .structure_collection import StructureCollection
        sc = StructureCollection(lines, **kwargs)
        sc.structures = mapping
        return sc
