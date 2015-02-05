import matplotlib.pyplot as plt
import numpy as np

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



def make_score_circles():
    """
    makes circles for displaying the foodfindr scores
    """

    from matplotlib.patches import Circle
    import matplotlib
    from matplotlib.collections import PatchCollection

    # Make 10 images, one for each 10% quantile of restaurants
    for ii in np.arange(11):

        # Set up plot
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.set_aspect(1)

        # Plot circle
        circ = Circle((0.,0.),1.)
        colors = [ii/10.]
        patches = [circ]
        p = PatchCollection(patches, cmap=matplotlib.cm.RdYlGn, alpha=0.7,lw=8)
        p.set_array(np.array(colors))
        p.set_clim([0.25,1.0])
        ax.add_collection(p)

        # Add text to the image
        #if ii < 9:
        #    tt = str(ii*10)+'-'+str((ii+1)*10)
        #else:
        #    tt = str(ii*10)+'+'
        #plt.text(0,0.05,tt,fontsize=84,ha='center',va='center')

        # Set up axes
        ax.set_ylim([-1.1,1.1])
        ax.set_xlim([-1.1,1.1])

        # Remove axis labels and tickes
        ax.set_xticks([])
        ax.set_yticks([])
        fig.patch.set_visible(False)
        ax.patch.set_visible(False)
        plt.axis('off')

        filename = '../app/static/images/ffcircle_'+str(float(ii)/2.)+'.png'
        plt.savefig(filename)

    return True
