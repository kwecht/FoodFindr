import matplotlib.pyplot as plt

def plot_class_results(frac2d):
    """
    Plot 2D matrix of classification predictions between [0,1]
    """
    fig = plt.figure()
    ax  = fig.add_subplot(111)
    matrix = ax.imshow(frac2d, cmap=plt.get_cmap('Greys'),interpolation='None',origin='lower')
    cb = plt.colorbar(matrix,ticks=[0,0.2,0.4,0.6,0.8,1.0])
    cb.ax.tick_params(labelsize=18) 
    ax.set_yticks([ii for ii in range(5)])
    ax.set_yticklabels([str(ii+1) for ii in range(5)], fontsize=20)
    ax.set_xticks([ii for ii in range(5)])
    ax.set_xticklabels([str(ii+1) for ii in range(5)], fontsize=20)
    ax.set_ylabel('Predicted Rating', fontsize=28)
    ax.set_xlabel('True Rating', fontsize=28)
    matrix.set_clim([0,1])
    fig_name = 'img/test_matrix.png'
    plt.savefig(fig_name,bbox_inches='tight')

    return True
