def plot_class_results(frac2d):
    """
    Plot 2D matrix of classification predictions between [0,1]
    """
    fig = plt.figure()
    ax  = fig.add_subplot(111)
    matrix = ax.imshow(frac2d, cmap=plt.get_cmap('PuBu'),interpolation='None',origin='lower')
    plt.colorbar(matrix)
    ax.set_yticks([ii for ii in range(5)])
    ax.set_yticklabels([str(ii+1) for ii in range(5)])
    ax.set_xticks([ii for ii in range(5)])
    ax.set_xticklabels([str(ii+1) for ii in range(5)])
    ax.set_ylabel('Predicted Stars')
    ax.set_xlabel('True Stars')
    matrix.set_clim([0,1])

    return True
